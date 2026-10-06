from unittest.mock import patch

from app.models import AtivoFixoSchema, AtivoVariavelSchema, ComparacaoRequestSchema, PerfilSchema
from app.services import comparacao_service
from app.services.llm_client import LlmIndisponivelError

CORRELATION_ID = "550e8400-e29b-41d4-a716-446655440000"


def perfil_dict():
    return dict(
        perfilRisco="MODERADO", horizonte="LONGO_PRAZO",
        objetivo="RENDA_PASSIVA", valorDisponivel=5000.0,
    )


def ativo_variavel_dict(codigo="TAEE3"):
    return dict(codigo=codigo, tipo="ACAO", setor="Energia", preco=38.42, dy=6.8, variacao30d=5.1)


def ativo_fixo_dict(codigo="TESOURO_SELIC_2029"):
    return dict(
        codigo=codigo, tipo="TESOURO", indexador="SELIC",
        taxaPercentual=100.0, vencimento="2029-01-01",
        investimentoMinimo=30.0, liquidez="DIARIA",
    )


@patch("app.services.comparacao_service.gerar_texto")
def test_gerar_veredito_deve_retornar_texto_do_llm_quando_sucesso(mock_gerar_texto):
    mock_gerar_texto.return_value = "TAEE3 tende a se encaixar melhor no seu perfil."

    request = ComparacaoRequestSchema(
        correlationId=CORRELATION_ID,
        perfil=PerfilSchema(**perfil_dict()),
        ativoA=AtivoVariavelSchema(**ativo_variavel_dict()),
        ativoB=AtivoFixoSchema(**ativo_fixo_dict()),
    )

    response = comparacao_service.gerar_veredito(request)

    assert str(response.correlationId) == CORRELATION_ID
    assert response.veredito == "TAEE3 tende a se encaixar melhor no seu perfil."
    assert response.erro is None


@patch("app.services.comparacao_service.gerar_texto")
def test_gerar_veredito_deve_usar_fallback_quando_llm_indisponivel(mock_gerar_texto):
    mock_gerar_texto.side_effect = LlmIndisponivelError("timeout")

    request = ComparacaoRequestSchema(
        correlationId=CORRELATION_ID,
        perfil=PerfilSchema(**perfil_dict()),
        ativoA=AtivoVariavelSchema(**ativo_variavel_dict(codigo="TAEE3")),
        ativoB=AtivoVariavelSchema(**ativo_variavel_dict(codigo="VALE3")),
    )

    response = comparacao_service.gerar_veredito(request)

    assert str(response.correlationId) == CORRELATION_ID
    assert "TAEE3" in response.veredito
    assert "VALE3" in response.veredito
    assert response.erro is not None


@patch("app.services.comparacao_service.gerar_texto")
def test_gerar_veredito_deve_funcionar_comparando_ativos_de_categorias_diferentes(mock_gerar_texto):
    mock_gerar_texto.return_value = "Comparação entre ação e título de renda fixa."

    request = ComparacaoRequestSchema(
        correlationId=CORRELATION_ID,
        perfil=PerfilSchema(**perfil_dict()),
        ativoA=AtivoVariavelSchema(**ativo_variavel_dict()),
        ativoB=AtivoFixoSchema(**ativo_fixo_dict()),
    )

    response = comparacao_service.gerar_veredito(request)

    mock_gerar_texto.assert_called_once()
    prompt_enviado = mock_gerar_texto.call_args.args[0]
    assert "TAEE3" in prompt_enviado
    assert "TESOURO_SELIC_2029" in prompt_enviado
    assert response.veredito == "Comparação entre ação e título de renda fixa."


ID_TITULO_PRIVADO = "f583a5d0-9cd4-4e23-a311-663954fb794d"


def titulo_privado_dict(**extras):
    return dict(
        codigo=ID_TITULO_PRIVADO, tipo="CDB", indexador="CDI",
        taxaPercentual=112.0, vencimento="2027-05-31",
        investimentoMinimo=500.0, liquidez="DIARIA", **extras,
    )


def request_com_titulo_privado(**extras):
    return ComparacaoRequestSchema(
        correlationId=CORRELATION_ID,
        perfil=PerfilSchema(**perfil_dict()),
        ativoA=AtivoVariavelSchema(**ativo_variavel_dict(codigo="PETR4")),
        ativoB=AtivoFixoSchema(**titulo_privado_dict(**extras)),
    )


@patch("app.services.comparacao_service.gerar_texto")
def test_gerar_veredito_deve_citar_o_nome_do_titulo_e_nao_o_id_no_fallback(mock_gerar_texto):
    mock_gerar_texto.side_effect = LlmIndisponivelError("timeout")

    response = comparacao_service.gerar_veredito(
        request_com_titulo_privado(nome="CDB - Banco Inter", emissor="Banco Inter"))

    assert "PETR4" in response.veredito
    assert "CDB - Banco Inter" in response.veredito
    assert ID_TITULO_PRIVADO not in response.veredito


@patch("app.services.comparacao_service.gerar_texto")
def test_gerar_veredito_deve_enviar_o_nome_do_titulo_e_nao_o_id_no_prompt(mock_gerar_texto):
    mock_gerar_texto.return_value = "Veredito."

    comparacao_service.gerar_veredito(
        request_com_titulo_privado(nome="CDB - Banco Inter", emissor="Banco Inter"))

    prompt_enviado = mock_gerar_texto.call_args.args[0]
    assert "ATIVO B (CDB - Banco Inter)" in prompt_enviado
    assert ID_TITULO_PRIVADO not in prompt_enviado


@patch("app.services.comparacao_service.gerar_texto")
def test_gerar_veredito_deve_usar_tipo_e_emissor_quando_o_titulo_nao_tem_nome(mock_gerar_texto):
    mock_gerar_texto.side_effect = LlmIndisponivelError("timeout")

    response = comparacao_service.gerar_veredito(request_com_titulo_privado(emissor="Banco Inter"))

    assert "CDB Banco Inter" in response.veredito
    assert ID_TITULO_PRIVADO not in response.veredito