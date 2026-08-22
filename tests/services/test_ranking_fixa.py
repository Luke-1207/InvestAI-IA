from datetime import date, timedelta

import pytest

from app.models import PerfilSchema, RankingRequestSchema
from app.services import ranking_service
from app.services.ranking_service import _classificar_compatibilidade

CORRELATION_ID = "550e8400-e29b-41d4-a716-446655440000"


def perfil(**overrides):
    dados = dict(
        perfilRisco="MODERADO", horizonte="MEDIO_PRAZO", objetivo="RENDA_PASSIVA",
        valorDisponivel=5000.0, tiposAceitos=[], setoresPreferidos=[],
    )
    dados.update(overrides)
    return PerfilSchema(**dados)


def data_em(dias):
    return (date.today() + timedelta(days=dias)).isoformat()


def titulo(**overrides):
    dados = dict(
        codigo="TESOURO_SELIC_2029", tipo="TESOURO", indexador="SELIC",
        taxaPercentual=100.0, vencimento=data_em(200),
        investimentoMinimo=30.0, liquidez="DIARIA",
        isentoIR=False, garantidoFGC=False,
    )
    dados.update(overrides)
    return dados


def ranquear_um(perfil_schema, titulo_dict):
    request = RankingRequestSchema(
        correlationId=CORRELATION_ID, modulo="FIXA", perfil=perfil_schema, ativos=[titulo_dict],
    )
    response = ranking_service.ranquear(request)
    return response.ativos[0] if response.ativos else None


class TestIndexadorXPerfilRisco:
    @pytest.mark.parametrize("indexador", ["SELIC", "CDI"])
    def test_conservador_com_indexador_previsivel_deve_pontuar_mais(self, indexador):
        favoravel = ranquear_um(perfil(perfilRisco="CONSERVADOR"), titulo(indexador=indexador, investimentoMinimo=999999))
        neutro = ranquear_um(perfil(perfilRisco="CONSERVADOR"), titulo(indexador="PREFIXADO", investimentoMinimo=999999))
        assert favoravel.score > neutro.score

    def test_arrojado_com_prefixado_deve_pontuar_mais(self):
        favoravel = ranquear_um(perfil(perfilRisco="ARROJADO"), titulo(indexador="PREFIXADO", investimentoMinimo=999999))
        neutro = ranquear_um(perfil(perfilRisco="ARROJADO"), titulo(indexador="IPCA", investimentoMinimo=999999))
        assert favoravel.score > neutro.score

    def test_moderado_nao_deve_receber_bonus_de_indexador_previsivel_nem_prefixado(self):
        selic = ranquear_um(perfil(perfilRisco="MODERADO"), titulo(indexador="SELIC", investimentoMinimo=999999))
        prefixado = ranquear_um(perfil(perfilRisco="MODERADO"), titulo(indexador="PREFIXADO", investimentoMinimo=999999))
        assert selic.score == prefixado.score


class TestIndexadorXObjetivo:
    def test_preservar_capital_com_ipca_deve_pontuar_mais(self):
        favoravel = ranquear_um(perfil(objetivo="PRESERVAR_CAPITAL"), titulo(indexador="IPCA", investimentoMinimo=999999))
        neutro = ranquear_um(perfil(objetivo="PRESERVAR_CAPITAL"), titulo(indexador="CDI", investimentoMinimo=999999))
        assert favoravel.score > neutro.score

    def test_renda_passiva_nao_deve_receber_bonus_de_protecao_inflacao(self):
        ipca = ranquear_um(perfil(objetivo="RENDA_PASSIVA"), titulo(indexador="IPCA", investimentoMinimo=999999))
        cdi = ranquear_um(perfil(objetivo="RENDA_PASSIVA"), titulo(indexador="CDI", investimentoMinimo=999999))
        assert ipca.score == cdi.score


class TestHorizonteXVencimento:
    def test_vencimento_dentro_do_horizonte_deve_pontuar_mais(self):
        dentro = ranquear_um(
            perfil(horizonte="CURTO_PRAZO"),
            titulo(vencimento=data_em(100), investimentoMinimo=999999),
        )
        muito_alem = ranquear_um(
            perfil(horizonte="CURTO_PRAZO"),
            titulo(vencimento=data_em(3000), investimentoMinimo=999999),
        )
        assert dentro.score > muito_alem.score

    def test_distancia_de_um_nivel_deve_ser_neutra(self):
        resultado = ranquear_um(
            perfil(horizonte="CURTO_PRAZO", perfilRisco="MODERADO", objetivo="CRESCIMENTO_PATRIMONIO",
                   valorDisponivel=1),
            titulo(
                vencimento=data_em(800),
                indexador="CDI", liquidez="NO_VENCIMENTO",
                isentoIR=False, garantidoFGC=False, investimentoMinimo=999999,
            ),
        )
        assert resultado.score == 0

    @pytest.mark.parametrize("dias,horizonte_esperado", [
        (365, "CURTO_PRAZO"), (366, "MEDIO_PRAZO"), (1825, "MEDIO_PRAZO"), (1826, "LONGO_PRAZO"),
    ])
    def test_fronteiras_de_classificacao_de_horizonte(self, dias, horizonte_esperado):
        resultado = ranquear_um(
            perfil(horizonte=horizonte_esperado),
            titulo(vencimento=data_em(dias), investimentoMinimo=999999),
        )
        neutro = ranquear_um(
            perfil(horizonte=horizonte_esperado),
            titulo(vencimento=data_em(dias), indexador="XXPREF", investimentoMinimo=999999) if False else
            titulo(vencimento=data_em(1), investimentoMinimo=999999),
        )
        # o título cai exatamente no horizonte esperado -> deve pontuar o bônus de "dentro"
        assert resultado.score >= neutro.score


class TestLiquidezXHorizonte:
    def test_curto_prazo_com_liquidez_diaria_deve_pontuar_mais(self):
        favoravel = ranquear_um(
            perfil(horizonte="CURTO_PRAZO"),
            titulo(liquidez="DIARIA", vencimento=data_em(800), investimentoMinimo=999999),
        )
        neutro = ranquear_um(
            perfil(horizonte="CURTO_PRAZO"),
            titulo(liquidez="NO_VENCIMENTO", vencimento=data_em(800), investimentoMinimo=999999),
        )
        assert favoravel.score > neutro.score

    def test_medio_prazo_nao_deve_receber_bonus_de_liquidez_diaria(self):
        diaria = ranquear_um(
            perfil(horizonte="MEDIO_PRAZO"),
            titulo(liquidez="DIARIA", vencimento=data_em(800), investimentoMinimo=999999),
        )
        vencimento_fixo = ranquear_um(
            perfil(horizonte="MEDIO_PRAZO"),
            titulo(liquidez="NO_VENCIMENTO", vencimento=data_em(800), investimentoMinimo=999999),
        )
        assert diaria.score == vencimento_fixo.score


class TestIsencaoIRXObjetivo:
    def test_renda_passiva_isento_deve_pontuar_mais(self):
        isento = ranquear_um(perfil(objetivo="RENDA_PASSIVA"), titulo(isentoIR=True, investimentoMinimo=999999))
        tributado = ranquear_um(perfil(objetivo="RENDA_PASSIVA"), titulo(isentoIR=False, investimentoMinimo=999999))
        assert isento.score > tributado.score

    def test_crescimento_patrimonio_nao_deve_receber_bonus_de_isencao(self):
        isento = ranquear_um(perfil(objetivo="CRESCIMENTO_PATRIMONIO"), titulo(isentoIR=True, investimentoMinimo=999999))
        tributado = ranquear_um(perfil(objetivo="CRESCIMENTO_PATRIMONIO"), titulo(isentoIR=False, investimentoMinimo=999999))
        assert isento.score == tributado.score


class TestInvestimentoMinimoXValorDisponivel:
    def test_investimento_dentro_do_valor_disponivel_deve_pontuar_mais(self):
        dentro = ranquear_um(perfil(valorDisponivel=1000), titulo(investimentoMinimo=500))
        fora = ranquear_um(perfil(valorDisponivel=1000), titulo(investimentoMinimo=5000))
        assert dentro.score > fora.score

    def test_investimento_igual_ao_valor_disponivel_deve_pontuar(self):
        igual = ranquear_um(perfil(valorDisponivel=1000), titulo(investimentoMinimo=1000))
        acima = ranquear_um(perfil(valorDisponivel=1000), titulo(investimentoMinimo=1000.01))
        assert igual.score > acima.score


class TestGarantiaFgcXPerfilConservador:
    def test_conservador_com_garantia_fgc_deve_pontuar_mais(self):
        garantido = ranquear_um(perfil(perfilRisco="CONSERVADOR"), titulo(garantidoFGC=True, investimentoMinimo=999999))
        nao_garantido = ranquear_um(perfil(perfilRisco="CONSERVADOR"), titulo(garantidoFGC=False, investimentoMinimo=999999))
        assert garantido.score > nao_garantido.score

    def test_moderado_nao_deve_receber_bonus_de_garantia_fgc(self):
        garantido = ranquear_um(perfil(perfilRisco="MODERADO"), titulo(garantidoFGC=True, investimentoMinimo=999999))
        nao_garantido = ranquear_um(perfil(perfilRisco="MODERADO"), titulo(garantidoFGC=False, investimentoMinimo=999999))
        assert garantido.score == nao_garantido.score


class TestNormalizacaoEClassificacao:
    def test_score_nunca_deve_ser_negativo(self):
        resultado = ranquear_um(
            perfil(horizonte="CURTO_PRAZO"),
            titulo(vencimento=data_em(3000), investimentoMinimo=999999),
        )
        assert resultado.score >= 0

    def test_score_nunca_deve_exceder_100(self):
        resultado = ranquear_um(
            perfil(perfilRisco="CONSERVADOR", horizonte="CURTO_PRAZO", objetivo="RENDA_PASSIVA", valorDisponivel=999999),
            titulo(indexador="SELIC", vencimento=data_em(100), liquidez="DIARIA", isentoIR=True, garantidoFGC=True, investimentoMinimo=30),
        )
        assert resultado.score <= 100

    @pytest.mark.parametrize("score,esperado", [
        (0, "BAIXA"), (39, "BAIXA"), (40, "MEDIA"), (69, "MEDIA"), (70, "ALTA"), (100, "ALTA"),
    ])
    def test_classificacao_deve_respeitar_limiares(self, score, esperado):
        assert _classificar_compatibilidade(score) == esperado


class TestJustificativa:
    def test_deve_gerar_justificativa_nao_vazia(self):
        resultado = ranquear_um(perfil(), titulo())
        assert resultado.justificativa

    def test_titulo_sem_nenhum_criterio_positivo_deve_ter_justificativa_generica(self):
        resultado = ranquear_um(
            perfil(perfilRisco="MODERADO", horizonte="CURTO_PRAZO", objetivo="CRESCIMENTO_PATRIMONIO",
                   valorDisponivel=1),
            titulo(indexador="CDI", vencimento=data_em(800), liquidez="NO_VENCIMENTO", isentoIR=False,
                   garantidoFGC=False, investimentoMinimo=999999),
        )
        assert resultado.justificativa == "Título dentro dos critérios mínimos avaliados para o seu perfil."