import json
from unittest.mock import MagicMock, patch

from app.consumers.comparacao_consumer import processar_mensagem
from app.consumers.queues import COMPARACAO_RESPONSE_QUEUE


def _payload():
    return {
        "correlationId": "550e8400-e29b-41d4-a716-446655440000",
        "perfil": {
            "perfilRisco": "MODERADO",
            "horizonte": "LONGO_PRAZO",
            "objetivo": "RENDA_PASSIVA",
            "valorDisponivel": 5000.0,
        },
        "ativoA": {
            "codigo": "TAEE3", "tipo": "ACAO", "setor": "Energia",
            "preco": 38.42, "dy": 6.8, "variacao30d": 5.1,
        },
        "ativoB": {
            "codigo": "TESOURO_SELIC_2029", "tipo": "TESOURO", "indexador": "SELIC",
            "taxaPercentual": 100.0, "vencimento": "2029-01-01",
            "investimentoMinimo": 30.0, "liquidez": "DIARIA",
        },
    }


@patch("app.consumers.comparacao_consumer.comparacao_service.gerar_veredito")
def test_processar_mensagem_deve_publicar_o_veredito_gerado(mock_gerar_veredito):
    from app.models import ComparacaoResponseSchema

    mock_gerar_veredito.return_value = ComparacaoResponseSchema(
        correlationId="550e8400-e29b-41d4-a716-446655440000",
        veredito="TAEE3 combina mais com o seu perfil.",
        erro=None,
    )

    channel = MagicMock()
    body = json.dumps(_payload()).encode("utf-8")

    processar_mensagem(channel, body)

    channel.basic_publish.assert_called_once()
    kwargs = channel.basic_publish.call_args.kwargs
    assert kwargs["routing_key"] == COMPARACAO_RESPONSE_QUEUE

    resposta = json.loads(kwargs["body"])
    assert resposta["veredito"] == "TAEE3 combina mais com o seu perfil."
    assert resposta["erro"] is None


def test_processar_mensagem_com_payload_invalido_deve_publicar_erro():
    channel = MagicMock()
    payload_invalido = _payload()
    del payload_invalido["perfil"]["perfilRisco"]
    body = json.dumps(payload_invalido).encode("utf-8")

    processar_mensagem(channel, body)

    channel.basic_publish.assert_called_once()
    kwargs = channel.basic_publish.call_args.kwargs
    resposta = json.loads(kwargs["body"])
    assert resposta["erro"] is not None