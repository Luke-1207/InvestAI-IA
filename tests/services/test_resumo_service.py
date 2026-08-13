from unittest.mock import patch

from app.models import PerfilSchema, ResumoRequestSchema
from app.services import resumo_service
from app.services.llm_client import LlmIndisponivelError

CORRELATION_ID = "550e8400-e29b-41d4-a716-446655440000"


def perfil_dict():
    return dict(
        perfilRisco="MODERADO", horizonte="LONGO_PRAZO",
        objetivo="RENDA_PASSIVA", valorDisponivel=5000.0,
    )


def ativo_variavel_dict():
    return dict(codigo="TAEE3", tipo="ACAO", setor="Energia", preco=38.42, dy=6.8, variacao30d=5.1)


def ativo_fixo_dict():
    return dict(
        codigo="TESOURO_SELIC_2029", tipo="TESOURO", indexador="SELIC",
        taxaPercentual=100.0, vencimento="2029-01-01",
        investimentoMinimo=30.0, liquidez="DIARIA",
    )


@patch("app.services.resumo_service.gerar_texto")
def test_gerar_resumo_deve_retornar_texto_do_llm_quando_sucesso(mock_gerar_texto):
    mock_gerar_texto.return_value = "Resumo gerado pelo LLM."

    request = ResumoRequestSchema(
        correlationId=CORRELATION_ID, modulo="VARIAVEL",
        perfil=PerfilSchema(**perfil_dict()), ativo=ativo_variavel_dict(),
    )

    response = resumo_service.gerar_resumo(request)

    assert response.resumo == "Resumo gerado pelo LLM."
    assert response.erro is None


@patch("app.services.resumo_service.gerar_texto")
def test_gerar_resumo_deve_usar_fallback_quando_llm_indisponivel(mock_gerar_texto):
    mock_gerar_texto.side_effect = LlmIndisponivelError("timeout")

    request = ResumoRequestSchema(
        correlationId=CORRELATION_ID, modulo="VARIAVEL",
        perfil=PerfilSchema(**perfil_dict()), ativo=ativo_variavel_dict(),
    )

    response = resumo_service.gerar_resumo(request)

    assert response.resumo is not None
    assert "TAEE3" in response.resumo
    assert response.erro is not None


@patch("app.services.resumo_service.gerar_texto")
def test_gerar_resumo_deve_usar_template_de_renda_fixa_quando_modulo_fixa(mock_gerar_texto):
    mock_gerar_texto.return_value = "Resumo de renda fixa."

    request = ResumoRequestSchema(
        correlationId=CORRELATION_ID, modulo="FIXA",
        perfil=PerfilSchema(**perfil_dict()), ativo=ativo_fixo_dict(),
    )

    response = resumo_service.gerar_resumo(request)

    assert response.resumo == "Resumo de renda fixa."
    prompt_usado = mock_gerar_texto.call_args[0][0]
    assert "TÍTULO" in prompt_usado


@patch("app.services.resumo_service.gerar_texto")
def test_gerar_resumo_fallback_renda_fixa_deve_citar_o_codigo(mock_gerar_texto):
    mock_gerar_texto.side_effect = LlmIndisponivelError("timeout")

    request = ResumoRequestSchema(
        correlationId=CORRELATION_ID, modulo="FIXA",
        perfil=PerfilSchema(**perfil_dict()), ativo=ativo_fixo_dict(),
    )

    response = resumo_service.gerar_resumo(request)

    assert "TESOURO_SELIC_2029" in response.resumo