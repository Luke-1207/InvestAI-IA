import json
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.consumers.queues import RANKING_RESPONSE_QUEUE
from app.consumers.ranking_consumer import processar_mensagem


def _payload_fixa():
    vencimento = (date.today() + timedelta(days=100)).isoformat()
    return {
        "correlationId": "550e8400-e29b-41d4-a716-446655440000",
        "modulo": "FIXA",
        "perfil": {
            "perfilRisco": "CONSERVADOR",
            "horizonte": "CURTO_PRAZO",
            "objetivo": "PRESERVAR_CAPITAL",
            "valorDisponivel": 5000.0,
        },
        "ativos": [
            {
                "codigo": "TESOURO_SELIC_2029",
                "tipo": "TESOURO",
                "indexador": "SELIC",
                "taxaPercentual": 100.0,
                "vencimento": vencimento,
                "investimentoMinimo": 30.0,
                "liquidez": "DIARIA",
                "isentoIR": False,
                "garantidoFGC": True,
            }
        ],
    }


def test_processar_mensagem_deve_ranquear_titulo_de_renda_fixa_de_verdade():
    channel = MagicMock()
    body = json.dumps(_payload_fixa()).encode("utf-8")

    processar_mensagem(channel, body)

    channel.basic_publish.assert_called_once()
    kwargs = channel.basic_publish.call_args.kwargs
    assert kwargs["routing_key"] == RANKING_RESPONSE_QUEUE

    resposta = json.loads(kwargs["body"])
    ativo_rankeado = resposta["ativos"][0]

    assert ativo_rankeado["score"] > 50
    assert ativo_rankeado["codigo"] == "TESOURO_SELIC_2029"
    assert ativo_rankeado["justificativa"]


def test_processar_mensagem_com_payload_invalido_deve_publicar_erro():
    channel = MagicMock()
    payload_invalido = _payload_fixa()
    del payload_invalido["perfil"]["perfilRisco"]
    body = json.dumps(payload_invalido).encode("utf-8")

    processar_mensagem(channel, body)

    channel.basic_publish.assert_called_once()
    kwargs = channel.basic_publish.call_args.kwargs
    resposta = json.loads(kwargs["body"])
    assert resposta["erro"] is not None