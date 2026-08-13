import json
import logging

from pydantic import ValidationError

from app.consumers.queues import RANKING_REQUEST_QUEUE, RANKING_RESPONSE_QUEUE
from app.consumers.rabbitmq_connection import executar_consumer_com_reconexao, publicar_resposta
from app.models import RankingRequestSchema
from app.services import ranking_service

logger = logging.getLogger(__name__)

NOME_CONSUMER = "ranking_consumer"


def processar_mensagem(channel, body: bytes) -> None:
    correlation_id = None
    try:
        dados = json.loads(body)
        correlation_id = dados.get("correlationId")

        request = RankingRequestSchema.model_validate(dados)
        response = ranking_service.ranquear(request)

        publicar_resposta(channel, RANKING_RESPONSE_QUEUE, response.model_dump(mode="json"))
        logger.info(
            "[%s] Processado correlationId=%s (%d ativos rankeados)",
            NOME_CONSUMER, correlation_id, len(response.ativos),
        )

    except (json.JSONDecodeError, ValidationError) as e:
        logger.error("[%s] Payload inválido: %s", NOME_CONSUMER, e)
        if correlation_id:
            publicar_resposta(channel, RANKING_RESPONSE_QUEUE, {
                "correlationId": correlation_id,
                "ativos": [],
                "erro": f"Payload inválido: {str(e)}",
            })


def iniciar() -> None:
    executar_consumer_com_reconexao(RANKING_REQUEST_QUEUE, processar_mensagem, NOME_CONSUMER)