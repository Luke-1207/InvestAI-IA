import pika
from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["Health"])


def _verificar_rabbitmq() -> bool:
    """
    Conexão curta e isolada só para checagem de saúde — não reaproveita a
    conexão persistente dos consumers (essa nasce no INVAI-43), para não
    acoplar o health check ao ciclo de vida da conexão de consumo.
    """
    try:
        params = pika.URLParameters(settings.RABBITMQ_URL)
        params.socket_timeout = 2
        params.connection_attempts = 1

        connection = pika.BlockingConnection(params)
        connection.close()
        return True
    except Exception:
        return False


@router.get("/health", summary="Verifica a saúde do microsserviço e a conexão com o RabbitMQ")
def health_check():
    return {
        "status": "ok",
        "rabbitmq": _verificar_rabbitmq(),
    }