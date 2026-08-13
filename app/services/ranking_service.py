from typing import List

from app.models import (
    AtivoRankeadoSchema,
    AtivoVariavelSchema,
    PerfilSchema,
    RankingRequestSchema,
    RankingResponseSchema,
)
from app.models.enums import HorizonteInvestimento, ModuloRanking, ObjetivoFinanceiro, PreferenciaSetor
from app.services import ranking_config as cfg


def ranquear(request: RankingRequestSchema) -> RankingResponseSchema:
    if request.modulo == ModuloRanking.VARIAVEL:
        return _ranquear_renda_variavel(request)
    return _ranquear_stub_renda_fixa(request)


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


def _ranquear_stub_renda_fixa(request: RankingRequestSchema) -> RankingResponseSchema:
    """STUB TEMPORÁRIO para RENDA FIXA. Algoritmo real chega no INVAI-45."""
    ativos_rankeados = [
        AtivoRankeadoSchema(
            codigo=ativo.codigo,
            score=50,
            compatibilidade="MEDIA",
            justificativa="Stub temporário — algoritmo de renda fixa chega no INVAI-45.",
        )
        for ativo in request.ativos
    ]
    return RankingResponseSchema(correlationId=request.correlationId, ativos=ativos_rankeados)