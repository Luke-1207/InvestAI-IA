from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import create_app

client = TestClient(create_app(start_consumers=False))

def test_health_deve_retornar_status_ok_e_rabbitmq_true_quando_conexao_bem_sucedida():
    with patch("app.api.health.pika.BlockingConnection") as mock_connection:
        mock_connection.return_value = MagicMock()
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["rabbitmq"] is True


def test_health_deve_retornar_rabbitmq_false_quando_conexao_falha():
    with patch("app.api.health.pika.BlockingConnection", side_effect=Exception("conexão recusada")):
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["rabbitmq"] is False