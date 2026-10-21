from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import create_app

client = TestClient(create_app(start_consumers=False))

LLM_OK = {"disponivel": True, "provider": "groq", "modelo": "openai/gpt-oss-120b", "detalhe": None}


def test_health_deve_retornar_status_ok_e_rabbitmq_true_quando_conexao_bem_sucedida():
    with patch("app.api.health.pika.BlockingConnection") as mock_connection, \
            patch("app.api.health.verificar_llm", return_value=LLM_OK):
        mock_connection.return_value = MagicMock()
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["rabbitmq"] is True


def test_health_deve_retornar_rabbitmq_false_quando_conexao_falha():
    with patch("app.api.health.pika.BlockingConnection", side_effect=Exception("conexão recusada")), \
            patch("app.api.health.verificar_llm", return_value=LLM_OK):
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["rabbitmq"] is False


def test_health_deve_incluir_o_estado_do_llm():
    llm_fora = {"disponivel": False, "provider": "groq", "modelo": "openai/gpt-oss-120b",
                "detalhe": "O provedor recusou a chave de API"}
    with patch("app.api.health.pika.BlockingConnection", return_value=MagicMock()), \
            patch("app.api.health.verificar_llm", return_value=llm_fora):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["llm"] == llm_fora


def test_health_sem_forcar_deve_aceitar_o_resultado_guardado_do_llm():
    with patch("app.api.health.pika.BlockingConnection", return_value=MagicMock()), \
            patch("app.api.health.verificar_llm", return_value=LLM_OK) as mock_llm:
        client.get("/health")

    mock_llm.assert_called_once_with(forcar=False)


def test_health_com_forcar_deve_pedir_uma_verificacao_nova_do_llm():
    with patch("app.api.health.pika.BlockingConnection", return_value=MagicMock()), \
            patch("app.api.health.verificar_llm", return_value=LLM_OK) as mock_llm:
        response = client.get("/health", params={"forcar": "true"})

    assert response.status_code == 200
    mock_llm.assert_called_once_with(forcar=True)
