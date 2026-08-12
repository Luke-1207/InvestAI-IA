import pytest
from pydantic import ValidationError

from app.models.enums import ModuloRanking
from app.models.resumo import ResumoRequestSchema, ResumoResponseSchema

CORRELATION_ID = "550e8400-e29b-41d4-a716-446655440000"


def perfil_dict():
    return dict(
        perfilRisco="MODERADO", horizonte="LONGO_PRAZO",
        objetivo="RENDA_PASSIVA", valorDisponivel=5000.0,
    )


def ativo_variavel_resumo_dict():
    return dict(
        codigo="TAEE3", nome="Taesa", tipo="ACAO", setor="Energia Elétrica",
        preco=38.42, dy=6.8, pl=12.4, pvp=1.3, variacao30d=5.1,
        variacao52s={"min": 28.10, "max": 41.90}, mediaSetorialDY=5.2,
    )


def test_resumo_request_schema_aceita_ativo_variavel():
    request = ResumoRequestSchema(
        correlationId=CORRELATION_ID, modulo=ModuloRanking.VARIAVEL,
        perfil=perfil_dict(), ativo=ativo_variavel_resumo_dict(),
    )

    assert request.ativo.nome == "Taesa"
    assert request.ativo.variacao52s.max == 41.90


def test_resumo_response_schema_aceita_resumo_com_sucesso():
    response = ResumoResponseSchema(correlationId=CORRELATION_ID, resumo="Texto gerado...", erro=None)

    assert response.resumo is not None
    assert response.erro is None


def test_resumo_response_schema_aceita_fallback_com_erro():
    response = ResumoResponseSchema(correlationId=CORRELATION_ID, resumo=None, erro="Timeout na API do LLM")

    assert response.erro == "Timeout na API do LLM"


def test_resumo_response_schema_rejeita_correlation_id_ausente():
    with pytest.raises(ValidationError):
        ResumoResponseSchema(resumo="texto")