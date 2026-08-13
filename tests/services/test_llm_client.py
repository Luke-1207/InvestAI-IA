from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.llm_client import LlmIndisponivelError, gerar_texto


@patch("app.services.llm_client.settings")
@patch("app.services.llm_client.httpx.post")
def test_gerar_texto_deve_retornar_conteudo_quando_chamada_bem_sucedida(mock_post, mock_settings):
    mock_settings.LLM_PROVIDER = "groq"
    mock_settings.LLM_API_KEY = "chave-teste"
    mock_settings.LLM_MODEL = "llama-3.3-70b-versatile"

    resposta_mock = MagicMock()
    resposta_mock.json.return_value = {"choices": [{"message": {"content": "  Texto gerado.  "}}]}
    resposta_mock.raise_for_status = MagicMock()
    mock_post.return_value = resposta_mock

    resultado = gerar_texto("prompt qualquer")

    assert resultado == "Texto gerado."
    mock_post.assert_called_once()


@patch("app.services.llm_client.settings")
def test_gerar_texto_deve_lancar_erro_quando_provider_nao_suportado(mock_settings):
    mock_settings.LLM_PROVIDER = "anthropic"

    with pytest.raises(LlmIndisponivelError, match="não suportado"):
        gerar_texto("prompt qualquer")


@patch("app.services.llm_client.settings")
@patch("app.services.llm_client.httpx.post")
def test_gerar_texto_deve_lancar_erro_quando_timeout(mock_post, mock_settings):
    mock_settings.LLM_PROVIDER = "groq"
    mock_settings.LLM_API_KEY = "chave-teste"
    mock_settings.LLM_MODEL = "llama-3.3-70b-versatile"
    mock_post.side_effect = httpx.TimeoutException("timeout")

    with pytest.raises(LlmIndisponivelError):
        gerar_texto("prompt qualquer")


@patch("app.services.llm_client.settings")
@patch("app.services.llm_client.httpx.post")
def test_gerar_texto_deve_lancar_erro_quando_resposta_http_falha(mock_post, mock_settings):
    mock_settings.LLM_PROVIDER = "groq"
    mock_settings.LLM_API_KEY = "chave-teste"
    mock_settings.LLM_MODEL = "llama-3.3-70b-versatile"

    resposta_mock = MagicMock()
    resposta_mock.raise_for_status.side_effect = httpx.HTTPStatusError(
        "erro", request=MagicMock(), response=MagicMock(status_code=401)
    )
    mock_post.return_value = resposta_mock

    with pytest.raises(LlmIndisponivelError):
        gerar_texto("prompt qualquer")


@patch("app.services.llm_client.settings")
@patch("app.services.llm_client.httpx.post")
def test_gerar_texto_deve_lancar_erro_quando_payload_de_resposta_malformado(mock_post, mock_settings):
    mock_settings.LLM_PROVIDER = "groq"
    mock_settings.LLM_API_KEY = "chave-teste"
    mock_settings.LLM_MODEL = "llama-3.3-70b-versatile"

    resposta_mock = MagicMock()
    resposta_mock.json.return_value = {"formato": "inesperado"}
    resposta_mock.raise_for_status = MagicMock()
    mock_post.return_value = resposta_mock

    with pytest.raises(LlmIndisponivelError):
        gerar_texto("prompt qualquer")