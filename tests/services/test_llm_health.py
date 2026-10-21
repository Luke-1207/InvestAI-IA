from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services import llm_health


@pytest.fixture(autouse=True)
def configuracao_padrao(monkeypatch):
    llm_health.limpar_cache()
    monkeypatch.setattr(llm_health.settings, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(llm_health.settings, "LLM_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setattr(llm_health.settings, "LLM_API_KEY", "chave-teste")
    yield
    llm_health.limpar_cache()


def _resposta(status_code: int) -> MagicMock:
    resposta = MagicMock()
    resposta.status_code = status_code
    return resposta


def test_deve_consultar_o_modelo_configurado_sem_gastar_tokens():
    with patch("app.services.llm_health.httpx.get", return_value=_resposta(200)) as mock_get:
        resultado = llm_health.verificar_llm()

    assert resultado == {"disponivel": True, "provider": "groq", "modelo": "openai/gpt-oss-120b", "detalhe": None}
    url = mock_get.call_args.args[0]
    assert url == "https://api.groq.com/openai/v1/models/openai/gpt-oss-120b"
    assert mock_get.call_args.kwargs["headers"]["Authorization"] == "Bearer chave-teste"
    assert mock_get.call_args.kwargs["timeout"] == llm_health.TIMEOUT_SEGUNDOS


@pytest.mark.parametrize(
    "status_code, detalhe",
    [
        (401, "O provedor recusou a chave de API"),
        (403, "O provedor recusou a chave de API"),
        (404, "Modelo 'openai/gpt-oss-120b' não encontrado no provedor"),
        (429, "Limite de uso do provedor atingido"),
        (503, "O provedor respondeu HTTP 503"),
    ],
)
def test_deve_explicar_cada_tipo_de_falha_do_provedor(status_code, detalhe):
    with patch("app.services.llm_health.httpx.get", return_value=_resposta(status_code)):
        resultado = llm_health.verificar_llm()

    assert resultado["disponivel"] is False
    assert resultado["detalhe"] == detalhe


def test_sem_resposta_do_provedor_deve_marcar_como_indisponivel():
    with patch("app.services.llm_health.httpx.get", side_effect=httpx.ConnectTimeout("timeout")):
        resultado = llm_health.verificar_llm()

    assert resultado["disponivel"] is False
    assert resultado["detalhe"] == "O provedor do LLM não respondeu"


def test_sem_chave_configurada_nao_deve_chamar_o_provedor(monkeypatch):
    monkeypatch.setattr(llm_health.settings, "LLM_API_KEY", "")
    with patch("app.services.llm_health.httpx.get") as mock_get:
        resultado = llm_health.verificar_llm()

    mock_get.assert_not_called()
    assert resultado["disponivel"] is False
    assert resultado["detalhe"] == "Chave de API do LLM não configurada"


def test_provider_nao_suportado_deve_ser_informado(monkeypatch):
    monkeypatch.setattr(llm_health.settings, "LLM_PROVIDER", "openai")
    with patch("app.services.llm_health.httpx.get") as mock_get:
        resultado = llm_health.verificar_llm()

    mock_get.assert_not_called()
    assert resultado["detalhe"] == "Provider 'openai' não suportado"


def test_deve_reaproveitar_o_resultado_por_um_minuto(monkeypatch):
    relogio = iter([1000.0, 1030.0, 1061.0])
    monkeypatch.setattr(llm_health.time, "monotonic", lambda: next(relogio))
    with patch("app.services.llm_health.httpx.get", return_value=_resposta(200)) as mock_get:
        llm_health.verificar_llm()
        llm_health.verificar_llm()
        llm_health.verificar_llm()

    assert mock_get.call_count == 2

def test_forcar_deve_ignorar_o_resultado_guardado(monkeypatch):
    relogio = iter([1000.0, 1010.0])
    monkeypatch.setattr(llm_health.time, "monotonic", lambda: next(relogio))
    with patch("app.services.llm_health.httpx.get", return_value=_resposta(200)) as mock_get:
        llm_health.verificar_llm()
        llm_health.verificar_llm(forcar=True)

    assert mock_get.call_count == 2
