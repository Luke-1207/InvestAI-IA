import pytest
from pydantic import ValidationError

from app.models.enums import (
    Compatibilidade,
    HorizonteInvestimento,
    ModuloRanking,
    ObjetivoFinanceiro,
    PerfilRisco,
)
from app.models.ranking import AtivoRankeadoSchema, RankingRequestSchema, RankingResponseSchema

CORRELATION_ID = "550e8400-e29b-41d4-a716-446655440000"


def perfil_dict():
    return dict(
        perfilRisco=PerfilRisco.MODERADO,
        horizonte=HorizonteInvestimento.LONGO_PRAZO,
        objetivo=ObjetivoFinanceiro.RENDA_PASSIVA,
        valorDisponivel=5000.0,
        tiposAceitos=["ACAO", "FII"],
        setoresPreferidos=[{"setor": "Energia", "preferencia": "PREFERIR"}],
    )


def ativo_variavel_dict(codigo="TAEE3"):
    return dict(
        codigo=codigo, tipo="ACAO", setor="Energia Elétrica",
        preco=38.42, dy=6.8, variacao30d=5.1, volatilidade="BAIXA",
    )


def ativo_fixo_dict(codigo="TESOURO_SELIC_2029"):
    return dict(
        codigo=codigo, tipo="TESOURO", indexador="SELIC", taxaPercentual=100.0,
        vencimento="2029-01-01", investimentoMinimo=30.0, liquidez="DIARIA",
    )


def test_ranking_request_schema_aceita_payload_de_renda_variavel():
    request = RankingRequestSchema(
        correlationId=CORRELATION_ID, modulo=ModuloRanking.VARIAVEL,
        perfil=perfil_dict(), ativos=[ativo_variavel_dict()],
    )

    assert str(request.correlationId) == CORRELATION_ID
    assert len(request.ativos) == 1


def test_ranking_request_schema_aceita_payload_de_renda_fixa():
    request = RankingRequestSchema(
        correlationId=CORRELATION_ID, modulo=ModuloRanking.FIXA,
        perfil=perfil_dict(), ativos=[ativo_fixo_dict()],
    )

    assert request.ativos[0].tipo == "TESOURO"


def test_ranking_request_schema_rejeita_ativo_variavel_quando_modulo_fixa():
    with pytest.raises(ValidationError):
        RankingRequestSchema(
            correlationId=CORRELATION_ID, modulo=ModuloRanking.FIXA,
            perfil=perfil_dict(), ativos=[ativo_variavel_dict()],
        )


def test_ranking_request_schema_rejeita_ativo_fixo_quando_modulo_variavel():
    with pytest.raises(ValidationError):
        RankingRequestSchema(
            correlationId=CORRELATION_ID, modulo=ModuloRanking.VARIAVEL,
            perfil=perfil_dict(), ativos=[ativo_fixo_dict()],
        )


def test_ranking_request_schema_rejeita_correlation_id_invalido():
    with pytest.raises(ValidationError):
        RankingRequestSchema(
            correlationId="nao-e-um-uuid", modulo=ModuloRanking.VARIAVEL,
            perfil=perfil_dict(), ativos=[ativo_variavel_dict()],
        )


def test_ativo_rankeado_schema_aceita_score_no_limite_inferior_e_superior():
    baixo = AtivoRankeadoSchema(codigo="TAEE3", score=0, compatibilidade="BAIXA", justificativa="x")
    alto = AtivoRankeadoSchema(codigo="TAEE3", score=100, compatibilidade="ALTA", justificativa="x")

    assert baixo.score == 0
    assert alto.score == 100


def test_ativo_rankeado_schema_rejeita_score_acima_de_100():
    with pytest.raises(ValidationError):
        AtivoRankeadoSchema(codigo="TAEE3", score=101, compatibilidade=Compatibilidade.ALTA, justificativa="x")


def test_ativo_rankeado_schema_rejeita_score_negativo():
    with pytest.raises(ValidationError):
        AtivoRankeadoSchema(codigo="TAEE3", score=-1, compatibilidade=Compatibilidade.BAIXA, justificativa="x")


def test_ativo_rankeado_schema_rejeita_compatibilidade_invalida():
    with pytest.raises(ValidationError):
        AtivoRankeadoSchema(codigo="TAEE3", score=50, compatibilidade="MEDIANA", justificativa="x")


def test_ranking_response_schema_aceita_lista_de_ativos_rankeados():
    response = RankingResponseSchema(
        correlationId=CORRELATION_ID,
        ativos=[{"codigo": "TAEE3", "score": 87, "compatibilidade": "ALTA", "justificativa": "Boa combinação"}],
    )

    assert response.ativos[0].score == 87