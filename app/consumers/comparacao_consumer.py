import json
import logging

from pydantic import ValidationError

from app.consumers.queues import COMPARACAO_REQUEST_QUEUE, COMPARACAO_RESPONSE_QUEUE
from app.consumers.rabbitmq_connection import executar_consumer_com_reconexao, publicar_resposta
from app.models import ComparacaoRequestSchema
from app.services import comparacao_service

logger = logging.getLogger(__name__)

NOME_CONSUMER = "comparacao_consumer"


def processar_mensagem(channel, body: bytes) -> None:
    correlation_id = None
    try:
        dados = json.loads(body)
        correlation_id = dados.get("correlationId")

        request = ComparacaoRequestSchema.model_validate(dados)
        response = comparacao_service.gerar_veredito(request)

        publicar_resposta(channel, COMPARACAO_RESPONSE_QUEUE, response.model_dump(mode="json"))
        logger.info("[%s] Processado correlationId=%s", NOME_CONSUMER, correlation_id)

    except (json.JSONDecodeError, ValidationError) as e:
        logger.error("[%s] Payload inválido: %s", NOME_CONSUMER, e)
        if correlation_id:
            publicar_resposta(channel, COMPARACAO_RESPONSE_QUEUE, {
                "correlationId": correlation_id,
                "veredito": None,
                "erro": f"Payload inválido: {str(e)}",
            })


def iniciar() -> None:
    executar_consumer_com_reconexao(COMPARACAO_REQUEST_QUEUE, processar_mensagem, NOME_CONSUMER)