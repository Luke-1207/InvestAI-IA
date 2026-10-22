import pika
from fastapi import APIRouter

from app.config import settings
from app.services.llm_health import verificar_llm

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


@router.get("/health", summary="Verifica a saúde do microsserviço, a conexão com o RabbitMQ e o acesso ao LLM")
def health_check(forcar: bool = False):
    return {
        "status": "ok",
        "rabbitmq": _verificar_rabbitmq(),
        "llm": verificar_llm(forcar=forcar),
    }
