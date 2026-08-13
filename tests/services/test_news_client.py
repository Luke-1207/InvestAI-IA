from unittest.mock import MagicMock, patch

import httpx

from app.services.news_client import buscar_manchetes_recentes


@patch("app.services.news_client.settings")
def test_deve_retornar_lista_vazia_quando_sem_chave_configurada(mock_settings):
    mock_settings.NEWS_API_KEY = ""
    assert buscar_manchetes_recentes("Taesa") == []


@patch("app.services.news_client.settings")
@patch("app.services.news_client.httpx.get")
def test_deve_retornar_manchetes_quando_chamada_bem_sucedida(mock_get, mock_settings):
    mock_settings.NEWS_API_KEY = "chave-teste"
    resposta_mock = MagicMock()
    resposta_mock.raise_for_status = MagicMock()
    resposta_mock.json.return_value = {"articles": [{"title": "Manchete 1"}, {"title": "Manchete 2"}]}
    mock_get.return_value = resposta_mock

    resultado = buscar_manchetes_recentes("Taesa")

    assert resultado == ["Manchete 1", "Manchete 2"]


@patch("app.services.news_client.settings")
@patch("app.services.news_client.httpx.get")
def test_deve_retornar_lista_vazia_quando_falha_http(mock_get, mock_settings):
    mock_settings.NEWS_API_KEY = "chave-teste"
    mock_get.side_effect = httpx.HTTPError("falha de rede")

    assert buscar_manchetes_recentes("Taesa") == []


@patch("app.services.news_client.settings")
@patch("app.services.news_client.httpx.get")
def test_deve_ignorar_artigos_sem_titulo(mock_get, mock_settings):
    mock_settings.NEWS_API_KEY = "chave-teste"
    resposta_mock = MagicMock()
    resposta_mock.raise_for_status = MagicMock()
    resposta_mock.json.return_value = {"articles": [{"title": "Válida"}, {"sem_titulo": True}]}
    mock_get.return_value = resposta_mock

    assert buscar_manchetes_recentes("Taesa") == ["Válida"]