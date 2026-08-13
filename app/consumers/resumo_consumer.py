import json
import logging

from pydantic import ValidationError

from app.consumers.queues import RESUMO_REQUEST_QUEUE, RESUMO_RESPONSE_QUEUE
from app.consumers.rabbitmq_connection import executar_consumer_com_reconexao, publicar_resposta
from app.models import ResumoRequestSchema
from app.services import resumo_service

logger = logging.getLogger(__name__)

NOME_CONSUMER = "resumo_consumer"


def processar_mensagem(channel, body: bytes) -> None:
    correlation_id = None
    try:
        dados = json.loads(body)
        correlation_id = dados.get("correlationId")

        request = ResumoRequestSchema.model_validate(dados)
        response = resumo_service.gerar_resumo(request)

        publicar_resposta(channel, RESUMO_RESPONSE_QUEUE, response.model_dump(mode="json"))
        logger.info("[%s] Processado correlationId=%s", NOME_CONSUMER, correlation_id)

    except (json.JSONDecodeError, ValidationError) as e:
        logger.error("[%s] Payload inválido: %s", NOME_CONSUMER, e)
        if correlation_id:
            publicar_resposta(channel, RESUMO_RESPONSE_QUEUE, {
                "correlationId": correlation_id,
                "resumo": None,
                "erro": f"Payload inválido: {str(e)}",
            })


def iniciar() -> None:
    executar_consumer_com_reconexao(RESUMO_REQUEST_QUEUE, processar_mensagem, NOME_CONSUMER)