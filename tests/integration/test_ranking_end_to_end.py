import json
import threading
import time
import uuid

import pika
import pytest

from app.config import settings
from app.consumers import ranking_consumer
from app.consumers.queues import RANKING_REQUEST_QUEUE, RANKING_RESPONSE_QUEUE


def _rabbitmq_disponivel() -> bool:
    try:
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        connection.close()
        return True
    except Exception:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _rabbitmq_disponivel(),
        reason="RabbitMQ indisponível localmente — suba o container antes de rodar testes de integração.",
    ),
]


@pytest.fixture(scope="module", autouse=True)
def consumer_em_background():
    """
    Sobe o consumer real numa thread, do mesmo jeito que o main.py faz em
    produção. Se você já tiver a aplicação rodando em paralelo (uvicorn),
    sem problema — o RabbitMQ distribui a mensagem para qualquer um dos
    dois consumers concorrentes da mesma fila, e o teste só se importa
    com a resposta correta aparecer, não com quem processou.
    """
    thread = threading.Thread(target=ranking_consumer.iniciar, daemon=True)
    thread.start()
    time.sleep(1)
    yield


def _publicar_request(payload: dict) -> None:
    connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
    channel = connection.channel()
    channel.queue_declare(queue=RANKING_REQUEST_QUEUE, durable=True)
    channel.basic_publish(
        exchange="", routing_key=RANKING_REQUEST_QUEUE,
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
    )
    connection.close()


def _aguardar_resposta(correlation_id: str, timeout_segundos: int = 10) -> dict:
    """
    Faz polling na fila de resposta procurando o correlationId esperado.
    Nota: consome (e descarta) qualquer mensagem antiga que esteja parada
    na fila de resposta durante a busca — normal em ambiente de teste.
    """
    connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
    channel = connection.channel()
    channel.queue_declare(queue=RANKING_RESPONSE_QUEUE, durable=True)

    inicio = time.time()
    while time.time() - inicio < timeout_segundos:
        _, _, body = channel.basic_get(queue=RANKING_RESPONSE_QUEUE, auto_ack=True)
        if body:
            resposta = json.loads(body)
            if resposta.get("correlationId") == correlation_id:
                connection.close()
                return resposta
        time.sleep(0.3)

    connection.close()
    pytest.fail(f"Timeout aguardando resposta para correlationId={correlation_id}")


def test_ranqueamento_ponta_a_ponta_via_rabbitmq():
    correlation_id = str(uuid.uuid4())

    payload = {
        "correlationId": correlation_id,
        "modulo": "VARIAVEL",
        "perfil": {
            "perfilRisco": "MODERADO", "horizonte": "LONGO_PRAZO",
            "objetivo": "RENDA_PASSIVA", "valorDisponivel": 5000.0,
            "tiposAceitos": ["ACAO", "FII"],
            "setoresPreferidos": [{"setor": "Energia Elétrica", "preferencia": "PREFERIR"}],
        },
        "ativos": [
            {"codigo": "TAEE3", "tipo": "ACAO", "setor": "Energia Elétrica",
             "preco": 38.42, "dy": 6.8, "variacao30d": 5.1, "volatilidade": "MEDIA"},
        ],
    }

    _publicar_request(payload)
    resposta = _aguardar_resposta(correlation_id)

    assert resposta["correlationId"] == correlation_id
    assert resposta["erro"] is None
    assert len(resposta["ativos"]) == 1
    assert resposta["ativos"][0]["codigo"] == "TAEE3"
    assert resposta["ativos"][0]["score"] > 0
    assert resposta["ativos"][0]["compatibilidade"] in ("ALTA", "MEDIA", "BAIXA")


def test_ranqueamento_ponta_a_ponta_deve_filtrar_tipo_nao_aceito():
    correlation_id = str(uuid.uuid4())

    payload = {
        "correlationId": correlation_id,
        "modulo": "VARIAVEL",
        "perfil": {
            "perfilRisco": "MODERADO", "horizonte": "MEDIO_PRAZO",
            "objetivo": "RENDA_PASSIVA", "valorDisponivel": 5000.0,
            "tiposAceitos": ["FII"], "setoresPreferidos": [],
        },
        "ativos": [
            {"codigo": "TAEE3", "tipo": "ACAO", "setor": "Energia Elétrica",
             "preco": 38.42, "dy": 6.8, "variacao30d": 5.1, "volatilidade": "BAIXA"},
        ],
    }

    _publicar_request(payload)
    resposta = _aguardar_resposta(correlation_id)

    assert resposta["erro"] is None
    assert resposta["ativos"] == []