import json
import logging
import time
from typing import Callable

import pika
import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from app.config import settings
from app.consumers.queues import TODAS_AS_FILAS

logger = logging.getLogger(__name__)

BACKOFF_INICIAL_SEGUNDOS = 2
BACKOFF_MAXIMO_SEGUNDOS = 60


def _declarar_filas(channel: BlockingChannel) -> None:
    """Declara as 4 filas com durable=True — espelha o RabbitConfig do lado Java."""
    for fila in TODAS_AS_FILAS:
        channel.queue_declare(queue=fila, durable=True)


def publicar_resposta(channel: BlockingChannel, fila: str, payload: dict) -> None:
    channel.basic_publish(
        exchange="",
        routing_key=fila,
        body=json.dumps(payload, default=str),
        properties=pika.BasicProperties(
            delivery_mode=2,  # 2 = persistente, sobrevive a restart do RabbitMQ
            content_type="application/json",
        ),
    )


def executar_consumer_com_reconexao(
    nome_fila: str,
    processar_mensagem: Callable[[BlockingChannel, bytes], None],
    nome_consumer: str,
) -> None:
    """
    Mantém um consumer rodando indefinidamente numa fila, com reconexão
    automática e backoff exponencial em caso de queda da conexão.
    Deve rodar em sua própria thread — BlockingConnection não é
    thread-safe para ser compartilhada entre threads.
    """
    backoff = BACKOFF_INICIAL_SEGUNDOS

    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
            channel = connection.channel()
            _declarar_filas(channel)
            channel.basic_qos(prefetch_count=1)

            def _callback(ch, method, properties, body):
                try:
                    processar_mensagem(ch, body)
                except Exception:
                    logger.exception("[%s] Falha ao processar mensagem", nome_consumer)
                finally:
                    # Sempre confirma a mensagem, mesmo em falha — evita travar a fila
                    # com uma mensagem "presa". Erros de negócio são comunicados de
                    # volta via fila de resposta (campo "erro"), não via nack/reject.
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=nome_fila, on_message_callback=_callback)

            logger.info("[%s] Conectado ao RabbitMQ. Ouvindo fila '%s'...", nome_consumer, nome_fila)
            backoff = BACKOFF_INICIAL_SEGUNDOS  # reseta após reconexão bem-sucedida
            channel.start_consuming()

        except (pika.exceptions.AMQPConnectionError, pika.exceptions.StreamLostError) as e:
            logger.warning(
                "[%s] Conexão com RabbitMQ perdida (%s). Reconectando em %ds...",
                nome_consumer, e, backoff,
            )
            time.sleep(backoff)
            backoff = min(backoff * 2, BACKOFF_MAXIMO_SEGUNDOS)

        except Exception:
            logger.exception("[%s] Erro inesperado. Reconectando em %ds...", nome_consumer, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, BACKOFF_MAXIMO_SEGUNDOS)