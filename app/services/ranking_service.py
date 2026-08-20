from datetime import date
from typing import List

from app.models import (
    AtivoFixoSchema,
    AtivoRankeadoSchema,
    AtivoVariavelSchema,
    PerfilSchema,
    RankingRequestSchema,
    RankingResponseSchema,
)
from app.models.enums import (
    HorizonteInvestimento,
    Indexador,
    Liquidez,
    ModuloRanking,
    ObjetivoFinanceiro,
    PerfilRisco,
    PreferenciaSetor,
)
from app.services import ranking_config as cfg


def ranquear(request: RankingRequestSchema) -> RankingResponseSchema:
    if request.modulo == ModuloRanking.VARIAVEL:
        return _ranquear_renda_variavel(request)
    return _ranquear_renda_fixa(request)


def _ranquear_renda_variavel(request: RankingRequestSchema) -> RankingResponseSchema:
    perfil = request.perfil

    elegiveis: List[AtivoVariavelSchema] = [
        ativo for ativo in request.ativos
        if not perfil.tiposAceitos or ativo.tipo in perfil.tiposAceitos
    ]

    ativos_rankeados = [_rankear_ativo(ativo, perfil) for ativo in elegiveis]

    return RankingResponseSchema(correlationId=request.correlationId, ativos=ativos_rankeados)


def _rankear_ativo(ativo: AtivoVariavelSchema, perfil: PerfilSchema) -> AtivoRankeadoSchema:
    criterios = _avaliar_criterios(ativo, perfil)

    score_bruto = sum(criterios.values())
    score = max(cfg.SCORE_MINIMO, min(cfg.SCORE_MAXIMO, score_bruto))

    return AtivoRankeadoSchema(
        codigo=ativo.codigo,
        score=score,
        compatibilidade=_classificar_compatibilidade(score),
        justificativa=_gerar_justificativa(ativo, perfil, criterios),
    )


def _avaliar_criterios(ativo: AtivoVariavelSchema, perfil: PerfilSchema) -> dict:
    criterios: dict = {}

    if not perfil.tiposAceitos or ativo.tipo in perfil.tiposAceitos:
        criterios["tipo_aceito"] = cfg.PESOS["tipo_aceito"]

    if ativo.volatilidade is not None:
        combinacao = (perfil.perfilRisco, ativo.volatilidade)
        if combinacao in cfg.VOLATILIDADE_FAVORAVEL:
            criterios["volatilidade_favoravel"] = cfg.PESOS["volatilidade_favoravel"]
        elif combinacao in cfg.VOLATILIDADE_DESFAVORAVEL:
            criterios["volatilidade_desfavoravel"] = cfg.PESOS["volatilidade_desfavoravel"]

    if perfil.objetivo == ObjetivoFinanceiro.RENDA_PASSIVA and ativo.dy >= cfg.DY_MINIMO_RENDA_PASSIVA:
        criterios["dy_renda_passiva"] = cfg.PESOS["dy_renda_passiva"]
    elif perfil.objetivo == ObjetivoFinanceiro.CRESCIMENTO_PATRIMONIO and ativo.dy < cfg.DY_MAXIMO_CRESCIMENTO:
        criterios["dy_crescimento"] = cfg.PESOS["dy_crescimento"]

    if ativo.preco <= perfil.valorDisponivel:
        criterios["preco_acessivel"] = cfg.PESOS["preco_acessivel"]

    for setor_pref in perfil.setoresPreferidos:
        if setor_pref.setor.lower() == ativo.setor.lower():
            if setor_pref.preferencia == PreferenciaSetor.PREFERIR:
                criterios["setor_preferido"] = cfg.PESOS["setor_preferido"]
            elif setor_pref.preferencia == PreferenciaSetor.EVITAR:
                criterios["setor_evitado"] = cfg.PESOS["setor_evitado"]
            break

    if perfil.horizonte == HorizonteInvestimento.LONGO_PRAZO and ativo.dy < cfg.DY_MAXIMO_CRESCIMENTO:
        criterios["horizonte_longo_crescimento"] = cfg.PESOS["horizonte_longo_crescimento"]

    return criterios


def _classificar_compatibilidade(score: int) -> str:
    if score >= cfg.LIMIAR_ALTA:
        return "ALTA"
    if score >= cfg.LIMIAR_MEDIA:
        return "MEDIA"
    return "BAIXA"


_TEMPLATES_JUSTIFICATIVA = {
    "volatilidade_favoravel": lambda a, p: f"Volatilidade {a.volatilidade.value.lower()} alinhada ao perfil {p.perfilRisco.value.lower()}",
    "volatilidade_desfavoravel": lambda a, p: f"Volatilidade {a.volatilidade.value.lower()} pode não combinar com o perfil {p.perfilRisco.value.lower()}",
    "dy_renda_passiva": lambda a, p: f"DY de {a.dy}%, adequado ao objetivo de renda passiva",
    "dy_crescimento": lambda a, p: "Baixo DY sugere reinvestimento de lucro, alinhado ao crescimento patrimonial",
    "preco_acessivel": lambda a, p: "Preço compatível com o valor disponível informado",
    "setor_preferido": lambda a, p: f"Setor {a.setor} está entre os preferidos",
    "setor_evitado": lambda a, p: f"Setor {a.setor} está na lista de setores a evitar",
    "horizonte_longo_crescimento": lambda a, p: "Perfil de crescimento alinhado ao horizonte de longo prazo",
}


def _gerar_justificativa(ativo: AtivoVariavelSchema, perfil: PerfilSchema, criterios: dict) -> str:
    ordenados = sorted(criterios.items(), key=lambda item: abs(item[1]), reverse=True)

    frases = []
    for nome, _ in ordenados:
        gerador = _TEMPLATES_JUSTIFICATIVA.get(nome)
        if gerador is None:
            continue
        frases.append(gerador(ativo, perfil))
        if len(frases) == 2:
            break

    if not frases:
        return "Ativo dentro dos critérios mínimos avaliados para o seu perfil."
    return ". ".join(frases) + "."


def _ranquear_renda_fixa(request: RankingRequestSchema) -> RankingResponseSchema:
    perfil = request.perfil
    ativos_rankeados = [_rankear_titulo(titulo, perfil) for titulo in request.ativos]
    return RankingResponseSchema(correlationId=request.correlationId, ativos=ativos_rankeados)


def _rankear_titulo(titulo: AtivoFixoSchema, perfil: PerfilSchema) -> AtivoRankeadoSchema:
    criterios = _avaliar_criterios_fixa(titulo, perfil)

    score_bruto = sum(criterios.values())
    score = max(cfg.SCORE_MINIMO, min(cfg.SCORE_MAXIMO, score_bruto))

    return AtivoRankeadoSchema(
        codigo=titulo.codigo,
        score=score,
        compatibilidade=_classificar_compatibilidade(score),
        justificativa=_gerar_justificativa_fixa(titulo, perfil, criterios),
    )


def _avaliar_criterios_fixa(titulo: AtivoFixoSchema, perfil: PerfilSchema) -> dict:
    criterios: dict = {}

    if perfil.perfilRisco == PerfilRisco.CONSERVADOR and titulo.indexador in cfg.INDEXADORES_PREVISIVEIS:
        criterios["indexador_previsivel_conservador"] = cfg.PESOS_FIXA["indexador_previsivel_conservador"]

    if perfil.perfilRisco == PerfilRisco.ARROJADO and titulo.indexador == Indexador.PREFIXADO:
        criterios["indexador_arrojado_prefixado"] = cfg.PESOS_FIXA["indexador_arrojado_prefixado"]

    if perfil.objetivo == ObjetivoFinanceiro.PRESERVAR_CAPITAL and titulo.indexador == Indexador.IPCA:
        criterios["indexador_protege_inflacao"] = cfg.PESOS_FIXA["indexador_protege_inflacao"]

    distancia = _distancia_horizonte_vencimento(titulo.vencimento, perfil.horizonte)
    if distancia == 0:
        criterios["vencimento_dentro_horizonte"] = cfg.PESOS_FIXA["vencimento_dentro_horizonte"]
    elif distancia >= 2:
        criterios["vencimento_muito_alem_horizonte"] = cfg.PESOS_FIXA["vencimento_muito_alem_horizonte"]

    if perfil.horizonte == HorizonteInvestimento.CURTO_PRAZO and titulo.liquidez == Liquidez.DIARIA:
        criterios["liquidez_diaria_curto_prazo"] = cfg.PESOS_FIXA["liquidez_diaria_curto_prazo"]

    if perfil.objetivo == ObjetivoFinanceiro.RENDA_PASSIVA and titulo.isentoIR:
        criterios["isento_ir_renda_passiva"] = cfg.PESOS_FIXA["isento_ir_renda_passiva"]

    if titulo.investimentoMinimo <= perfil.valorDisponivel:
        criterios["investimento_acessivel"] = cfg.PESOS_FIXA["investimento_acessivel"]

    if perfil.perfilRisco == PerfilRisco.CONSERVADOR and titulo.garantidoFGC:
        criterios["garantia_fgc_conservador"] = cfg.PESOS_FIXA["garantia_fgc_conservador"]

    return criterios


def _classificar_horizonte_por_dias(dias: int) -> HorizonteInvestimento:
    if dias <= cfg.DIAS_LIMITE_CURTO_PRAZO:
        return HorizonteInvestimento.CURTO_PRAZO
    if dias <= cfg.DIAS_LIMITE_MEDIO_PRAZO:
        return HorizonteInvestimento.MEDIO_PRAZO
    return HorizonteInvestimento.LONGO_PRAZO


def _distancia_horizonte_vencimento(vencimento: date, horizonte_perfil: HorizonteInvestimento) -> int:
    dias = (vencimento - date.today()).days
    horizonte_titulo = _classificar_horizonte_por_dias(dias)
    return abs(cfg.HORIZONTE_ORDEM.index(horizonte_titulo) - cfg.HORIZONTE_ORDEM.index(horizonte_perfil))


_TEMPLATES_JUSTIFICATIVA_FIXA = {
    "indexador_previsivel_conservador": lambda t, p: f"Indexador {t.indexador.value} é previsível, alinhado ao perfil conservador",
    "indexador_arrojado_prefixado": lambda t, p: "Taxa prefixada é uma aposta compatível com o perfil arrojado",
    "indexador_protege_inflacao": lambda t, p: "Indexação ao IPCA protege o poder de compra, alinhado ao objetivo de preservar capital",
    "vencimento_dentro_horizonte": lambda t, p: f"Vencimento compatível com o horizonte de {p.horizonte.value.lower().replace('_', ' ')}",
    "vencimento_muito_alem_horizonte": lambda t, p: "Vencimento muito além do horizonte de investimento informado",
    "liquidez_diaria_curto_prazo": lambda t, p: "Liquidez diária é importante para quem pode precisar do dinheiro em breve",
    "isento_ir_renda_passiva": lambda t, p: "Isenção de Imposto de Renda favorece o objetivo de renda passiva",
    "investimento_acessivel": lambda t, p: "Investimento mínimo compatível com o valor disponível informado",
    "garantia_fgc_conservador": lambda t, p: "Garantia do FGC traz segurança adicional, alinhada ao perfil conservador",
}


def _gerar_justificativa_fixa(titulo: AtivoFixoSchema, perfil: PerfilSchema, criterios: dict) -> str:
    ordenados = sorted(criterios.items(), key=lambda item: abs(item[1]), reverse=True)

    frases = []
    for nome, _ in ordenados:
        gerador = _TEMPLATES_JUSTIFICATIVA_FIXA.get(nome)
        if gerador is None:
            continue
        frases.append(gerador(titulo, perfil))
        if len(frases) == 2:
            break

    if not frases:
        return "Título dentro dos critérios mínimos avaliados para o seu perfil."
    return ". ".join(frases) + "."