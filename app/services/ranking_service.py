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
    PreferenciaSetor,
    TipoAtivoFixo,
    Volatilidade,
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
    pesos = cfg.PESOS

    volatilidade = ativo.volatilidade or Volatilidade.MEDIA
    distancia = abs(cfg.ORDEM_RISCO.index(perfil.perfilRisco) - cfg.ORDEM_VOLATILIDADE.index(volatilidade))
    if distancia == 0:
        criterios["volatilidade_ideal"] = pesos["volatilidade_ideal"]
    elif distancia == 1:
        criterios["volatilidade_proxima"] = pesos["volatilidade_proxima"]
    elif volatilidade == Volatilidade.ALTA:
        criterios["volatilidade_alta_demais"] = pesos["volatilidade_oposta"]
    else:
        criterios["volatilidade_baixa_demais"] = pesos["volatilidade_oposta"]

    dy_alto = ativo.dy >= cfg.DY_ALTO
    dy_baixo = ativo.dy < cfg.DY_BAIXO
    if perfil.objetivo == ObjetivoFinanceiro.RENDA_PASSIVA:
        if dy_alto:
            criterios["dy_renda_passiva"] = pesos["dy_alinhado"]
        elif not dy_baixo:
            criterios["dy_renda_passiva_parcial"] = pesos["dy_parcial"]
    elif perfil.objetivo == ObjetivoFinanceiro.CRESCIMENTO_PATRIMONIO:
        if dy_baixo:
            criterios["dy_crescimento"] = pesos["dy_alinhado"]
        elif not dy_alto:
            criterios["dy_crescimento_parcial"] = pesos["dy_parcial"]
        else:
            criterios["dy_crescimento_fraco"] = pesos["dy_fraco"]
    elif not dy_baixo:
        criterios["dy_preservar"] = pesos["dy_alinhado"]
    else:
        criterios["dy_preservar_fraco"] = pesos["dy_fraco"]

    if perfil.horizonte == HorizonteInvestimento.LONGO_PRAZO:
        criterios["horizonte_longo"] = pesos["horizonte_longo"]
    elif perfil.horizonte == HorizonteInvestimento.MEDIO_PRAZO:
        criterios["horizonte_medio"] = pesos["horizonte_medio"]

    if ativo.preco <= perfil.valorDisponivel:
        criterios["preco_acessivel"] = pesos["preco_acessivel"]

    preferencia = _preferencia_do_setor(ativo.setor, perfil)
    if preferencia == PreferenciaSetor.PREFERIR:
        criterios["setor_preferido"] = pesos["setor_preferido"]
    elif preferencia == PreferenciaSetor.EVITAR:
        criterios["setor_evitado"] = pesos["setor_evitado"]
    else:
        criterios["setor_neutro"] = pesos["setor_neutro"]

    return criterios


def _preferencia_do_setor(setor: str, perfil: PerfilSchema):
    for setor_pref in perfil.setoresPreferidos:
        if setor_pref.setor.lower() == setor.lower():
            return setor_pref.preferencia
    return None


def _classificar_compatibilidade(score: int) -> str:
    if score >= cfg.LIMIAR_ALTA:
        return "ALTA"
    if score >= cfg.LIMIAR_MEDIA:
        return "MEDIA"
    return "BAIXA"


_TEMPLATES_JUSTIFICATIVA = {
    "volatilidade_ideal": lambda a, p: "Oscilação de preço compatível com o seu perfil de risco",
    "volatilidade_proxima": lambda a, p: "Oscilação de preço aceitável para o seu perfil de risco",
    "volatilidade_alta_demais": lambda a, p: "Oscila mais do que o seu perfil de risco costuma tolerar",
    "volatilidade_baixa_demais": lambda a, p: "Oscila pouco, com potencial de retorno abaixo do que o seu perfil busca",
    "dy_renda_passiva": lambda a, p: f"DY de {a.dy}%, alinhado ao seu objetivo de renda passiva",
    "dy_renda_passiva_parcial": lambda a, p: "Paga dividendos moderados, o que ajuda no objetivo de renda passiva",
    "dy_crescimento": lambda a, p: "Baixo DY sugere reinvestimento do lucro, alinhado ao crescimento de patrimônio",
    "dy_crescimento_parcial": lambda a, p: "Combina dividendos moderados com espaço para crescer",
    "dy_preservar": lambda a, p: "Distribui parte do lucro aos acionistas, característica de empresas mais maduras",
    "horizonte_longo": lambda a, p: "Renda variável combina com o seu horizonte de longo prazo",
    "horizonte_medio": lambda a, p: "Seu horizonte de médio prazo comporta uma parte em renda variável",
    "preco_acessivel": lambda a, p: "Preço compatível com o valor que você tem disponível",
    "setor_preferido": lambda a, p: f"Setor {a.setor} está entre os que você prefere",
    "setor_evitado": lambda a, p: f"Setor {a.setor} está entre os que você prefere evitar",
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
    pesos = cfg.PESOS_FIXA

    peso_indexador = cfg.PESO_INDEXADOR[perfil.perfilRisco][titulo.indexador]
    if peso_indexador == pesos["indexador_ideal"]:
        criterios["indexador_ideal"] = peso_indexador
    elif peso_indexador >= 20:
        criterios["indexador_adequado"] = peso_indexador
    else:
        criterios["indexador_aceitavel"] = peso_indexador

    distancia = _distancia_horizonte_vencimento(titulo.vencimento, perfil.horizonte)
    if distancia == 0:
        criterios["vencimento_no_horizonte"] = pesos["vencimento_no_horizonte"]
    elif distancia == 1:
        criterios["vencimento_proximo_horizonte"] = pesos["vencimento_proximo_horizonte"]
    else:
        criterios["vencimento_muito_alem_horizonte"] = pesos["vencimento_muito_alem_horizonte"]

    if titulo.liquidez == Liquidez.DIARIA:
        criterios["liquidez_diaria"] = pesos["liquidez_adequada"]
    elif perfil.horizonte == HorizonteInvestimento.LONGO_PRAZO:
        criterios["liquidez_no_vencimento_longo"] = pesos["liquidez_adequada"]
    elif perfil.horizonte == HorizonteInvestimento.MEDIO_PRAZO:
        criterios["liquidez_no_vencimento_medio"] = pesos["liquidez_parcial"]

    pos_fixado = titulo.indexador in cfg.INDEXADORES_POS_FIXADOS
    if perfil.objetivo == ObjetivoFinanceiro.RENDA_PASSIVA:
        if titulo.isentoIR:
            criterios["isento_ir_renda_passiva"] = pesos["objetivo_alinhado"]
        else:
            criterios["renda_passiva_tributada"] = pesos["objetivo_fraco"]
    elif perfil.objetivo == ObjetivoFinanceiro.PRESERVAR_CAPITAL:
        if titulo.indexador == Indexador.IPCA:
            criterios["indexador_protege_inflacao"] = pesos["objetivo_alinhado"]
        elif pos_fixado:
            criterios["pos_fixado_preservar"] = pesos["objetivo_pos_fixado_preservar"]
        else:
            criterios["prefixado_preservar"] = pesos["objetivo_fraco"]
    elif pos_fixado:
        criterios["pos_fixado_crescimento"] = pesos["objetivo_parcial"]
    else:
        criterios["taxa_crescimento"] = pesos["objetivo_alinhado"]

    if titulo.investimentoMinimo <= perfil.valorDisponivel:
        criterios["investimento_acessivel"] = pesos["investimento_acessivel"]

    if titulo.tipo == TipoAtivoFixo.TESOURO:
        criterios["garantia_tesouro"] = pesos["garantia"]
    elif titulo.garantidoFGC:
        criterios["garantia_fgc"] = pesos["garantia"]

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
    "indexador_ideal": lambda t, p: f"Indexador {t.indexador.value} é o mais indicado para o perfil {p.perfilRisco.value.lower()}",
    "indexador_adequado": lambda t, p: f"Indexador {t.indexador.value} combina bem com o perfil {p.perfilRisco.value.lower()}",
    "vencimento_no_horizonte": lambda t, p: f"Vencimento compatível com o horizonte de {p.horizonte.value.lower().replace('_', ' ')}",
    "vencimento_proximo_horizonte": lambda t, p: "Vencimento um pouco diferente do seu horizonte, mas ainda razoável",
    "vencimento_muito_alem_horizonte": lambda t, p: "Vencimento muito distante do horizonte que você informou",
    "liquidez_diaria": lambda t, p: "Liquidez diária, você pode resgatar quando precisar",
    "liquidez_no_vencimento_longo": lambda t, p: "Resgate só no vencimento, sem problema para o seu horizonte de longo prazo",
    "isento_ir_renda_passiva": lambda t, p: "Isenção de Imposto de Renda favorece o objetivo de renda passiva",
    "indexador_protege_inflacao": lambda t, p: "Indexação ao IPCA protege o poder de compra, alinhado a preservar capital",
    "pos_fixado_preservar": lambda t, p: "Rendimento que acompanha os juros, estável para preservar capital",
    "taxa_crescimento": lambda t, p: "Taxa prefixada ou ligada à inflação favorece o crescimento no longo prazo",
    "investimento_acessivel": lambda t, p: "Investimento mínimo compatível com o valor disponível informado",
    "garantia_tesouro": lambda t, p: "Título público, garantido pelo Tesouro Nacional",
    "garantia_fgc": lambda t, p: "Garantia do FGC traz segurança adicional",
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