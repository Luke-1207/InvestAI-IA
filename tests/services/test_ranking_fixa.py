from datetime import date, timedelta

import pytest

from app.models import PerfilSchema, RankingRequestSchema
from app.services import ranking_config as cfg
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


class TestPesos:
    def test_soma_dos_melhores_criterios_deve_fechar_100(self):
        p = cfg.PESOS_FIXA
        maximo = (p["indexador_ideal"] + p["vencimento_no_horizonte"] + p["liquidez_adequada"]
                  + p["objetivo_alinhado"] + p["investimento_acessivel"] + p["garantia"])
        assert maximo == 100

    def test_todo_perfil_de_risco_deve_ter_um_indexador_ideal(self):
        for risco, pesos in cfg.PESO_INDEXADOR.items():
            assert max(pesos.values()) == cfg.PESOS_FIXA["indexador_ideal"], risco


class TestCenariosIguaisAoJava:
    """Mesmos cenários de RendaFixaPontuacaoServiceTest, para garantir que os dois motores dão a mesma leitura."""

    def test_arrojado_com_tesouro_prefixado_longo_deve_chegar_a_100(self):
        resultado = ranquear_um(
            perfil(perfilRisco="ARROJADO", horizonte="LONGO_PRAZO", objetivo="CRESCIMENTO_PATRIMONIO", valorDisponivel=9999),
            titulo(tipo="TESOURO", indexador="PREFIXADO", vencimento=data_em(3000), liquidez="DIARIA", investimentoMinimo=30),
        )
        assert resultado.score == 100

    def test_conservador_de_curto_prazo_com_tesouro_selic_deve_ser_alta(self):
        resultado = ranquear_um(
            perfil(perfilRisco="CONSERVADOR", horizonte="CURTO_PRAZO", objetivo="RENDA_PASSIVA", valorDisponivel=9999),
            titulo(tipo="TESOURO", indexador="SELIC", vencimento=data_em(100), liquidez="DIARIA", investimentoMinimo=150),
        )
        assert resultado.score == 90
        assert resultado.compatibilidade == "ALTA"

    def test_moderado_agora_pode_chegar_a_alta(self):
        resultado = ranquear_um(
            perfil(perfilRisco="MODERADO", horizonte="LONGO_PRAZO", objetivo="PRESERVAR_CAPITAL", valorDisponivel=500),
            titulo(tipo="CDB", indexador="IPCA", vencimento=data_em(2500), liquidez="NO_VENCIMENTO",
                   garantidoFGC=True, investimentoMinimo=1000),
        )
        assert resultado.score == 90
        assert resultado.compatibilidade == "ALTA"

    def test_combinacao_parcial_deve_ser_media(self):
        resultado = ranquear_um(
            perfil(perfilRisco="MODERADO", horizonte="MEDIO_PRAZO", objetivo="CRESCIMENTO_PATRIMONIO", valorDisponivel=5000),
            titulo(tipo="LCI", indexador="CDI", vencimento=data_em(1000), liquidez="NO_VENCIMENTO",
                   isentoIR=True, garantidoFGC=True, investimentoMinimo=1000),
        )
        assert resultado.score == 76
        assert resultado.compatibilidade == "MEDIA"

    def test_titulo_que_nao_combina_deve_ser_baixa(self):
        resultado = ranquear_um(
            perfil(perfilRisco="CONSERVADOR", horizonte="CURTO_PRAZO", objetivo="CRESCIMENTO_PATRIMONIO", valorDisponivel=1000),
            titulo(tipo="CDB", indexador="PREFIXADO", vencimento=data_em(3000), liquidez="NO_VENCIMENTO",
                   garantidoFGC=False, investimentoMinimo=5000),
        )
        assert resultado.score == 10
        assert resultado.compatibilidade == "BAIXA"

    def test_renda_passiva_deve_preferir_titulos_isentos(self):
        base = perfil(perfilRisco="MODERADO", horizonte="MEDIO_PRAZO", objetivo="RENDA_PASSIVA", valorDisponivel=9999)
        isento = ranquear_um(base, titulo(tipo="LCA", indexador="CDI", vencimento=data_em(1000), liquidez="NO_VENCIMENTO",
                                          isentoIR=True, garantidoFGC=True, investimentoMinimo=1000))
        tributado = ranquear_um(base, titulo(tipo="CDB", indexador="CDI", vencimento=data_em(1000), liquidez="NO_VENCIMENTO",
                                             garantidoFGC=True, investimentoMinimo=1000))
        assert isento.score - tributado.score == 10


class TestIndexadorXPerfilRisco:
    @pytest.mark.parametrize("risco,melhor,pior", [
        ("CONSERVADOR", "SELIC", "PREFIXADO"),
        ("CONSERVADOR", "CDI", "IPCA"),
        ("MODERADO", "IPCA", "CDI"),
        ("ARROJADO", "PREFIXADO", "SELIC"),
    ])
    def test_cada_perfil_deve_preferir_o_seu_indexador(self, risco, melhor, pior):
        a = ranquear_um(perfil(perfilRisco=risco, objetivo="RENDA_PASSIVA"), titulo(indexador=melhor))
        b = ranquear_um(perfil(perfilRisco=risco, objetivo="RENDA_PASSIVA"), titulo(indexador=pior))
        assert a.score > b.score


class TestIndexadorXObjetivo:
    def test_preservar_capital_deve_dar_o_bonus_de_inflacao_ao_ipca(self):
        ipca = ranquear_um(perfil(perfilRisco="MODERADO", objetivo="PRESERVAR_CAPITAL"), titulo(indexador="IPCA"))
        cdi = ranquear_um(perfil(perfilRisco="MODERADO", objetivo="PRESERVAR_CAPITAL"), titulo(indexador="CDI"))
        assert ipca.score - cdi.score == 15

    def test_para_o_conservador_o_pos_fixado_segue_na_frente_mesmo_preservando_capital(self):
        ipca = ranquear_um(perfil(perfilRisco="CONSERVADOR", objetivo="PRESERVAR_CAPITAL"), titulo(indexador="IPCA"))
        cdi = ranquear_um(perfil(perfilRisco="CONSERVADOR", objetivo="PRESERVAR_CAPITAL"), titulo(indexador="CDI"))
        assert cdi.score - ipca.score == 10

    def test_crescimento_deve_preferir_taxa_travada_ou_inflacao(self):
        prefixado = ranquear_um(perfil(perfilRisco="MODERADO", objetivo="CRESCIMENTO_PATRIMONIO"), titulo(indexador="PREFIXADO"))
        cdi = ranquear_um(perfil(perfilRisco="MODERADO", objetivo="CRESCIMENTO_PATRIMONIO"), titulo(indexador="CDI"))
        assert prefixado.score - cdi.score == 7


class TestHorizonteXVencimento:
    def test_vencimento_dentro_do_horizonte_deve_pontuar_mais(self):
        dentro = ranquear_um(perfil(horizonte="CURTO_PRAZO"), titulo(vencimento=data_em(100)))
        muito_alem = ranquear_um(perfil(horizonte="CURTO_PRAZO"), titulo(vencimento=data_em(3000)))
        assert dentro.score - muito_alem.score == 35

    def test_distancia_de_um_nivel_deve_dar_pontuacao_parcial(self):
        dentro = ranquear_um(perfil(horizonte="CURTO_PRAZO"), titulo(vencimento=data_em(100)))
        vizinho = ranquear_um(perfil(horizonte="CURTO_PRAZO"), titulo(vencimento=data_em(800)))
        assert dentro.score - vizinho.score == 15

    @pytest.mark.parametrize("dias,horizonte_esperado", [
        (365, "CURTO_PRAZO"), (366, "MEDIO_PRAZO"), (1825, "MEDIO_PRAZO"), (1826, "LONGO_PRAZO"),
    ])
    def test_fronteiras_de_classificacao_de_horizonte(self, dias, horizonte_esperado):
        criterios = ranking_service._avaliar_criterios_fixa(
            ranking_service.AtivoFixoSchema(**titulo(vencimento=data_em(dias))), perfil(horizonte=horizonte_esperado))
        assert "vencimento_no_horizonte" in criterios


class TestLiquidezXHorizonte:
    @pytest.mark.parametrize("horizonte,pontos_no_vencimento", [
        ("CURTO_PRAZO", 0), ("MEDIO_PRAZO", 8), ("LONGO_PRAZO", 15),
    ])
    def test_resgate_so_no_vencimento_pesa_menos_quanto_mais_curto_o_horizonte(self, horizonte, pontos_no_vencimento):
        diaria = ranquear_um(perfil(horizonte=horizonte), titulo(liquidez="DIARIA", vencimento=data_em(800)))
        no_vencimento = ranquear_um(perfil(horizonte=horizonte), titulo(liquidez="NO_VENCIMENTO", vencimento=data_em(800)))
        assert diaria.score - no_vencimento.score == 15 - pontos_no_vencimento


class TestInvestimentoMinimoXValorDisponivel:
    def test_investimento_dentro_do_valor_disponivel_deve_pontuar_mais(self):
        dentro = ranquear_um(perfil(valorDisponivel=1000), titulo(investimentoMinimo=500))
        fora = ranquear_um(perfil(valorDisponivel=1000), titulo(investimentoMinimo=5000))
        assert dentro.score - fora.score == 10

    def test_investimento_igual_ao_valor_disponivel_deve_pontuar(self):
        igual = ranquear_um(perfil(valorDisponivel=1000), titulo(investimentoMinimo=1000))
        acima = ranquear_um(perfil(valorDisponivel=1000), titulo(investimentoMinimo=1000.01))
        assert igual.score > acima.score


class TestGarantia:
    def test_tesouro_e_titulo_com_fgc_devem_somar_a_garantia(self):
        tesouro = ranquear_um(perfil(), titulo(tipo="TESOURO"))
        cdb_fgc = ranquear_um(perfil(), titulo(tipo="CDB", garantidoFGC=True))
        cdb_sem = ranquear_um(perfil(), titulo(tipo="CDB", garantidoFGC=False))
        assert tesouro.score == cdb_fgc.score == cdb_sem.score + 5


class TestNormalizacaoEClassificacao:
    def test_score_nunca_deve_ser_negativo(self):
        resultado = ranquear_um(
            perfil(perfilRisco="CONSERVADOR", horizonte="CURTO_PRAZO", objetivo="PRESERVAR_CAPITAL", valorDisponivel=1),
            titulo(tipo="CDB", indexador="PREFIXADO", vencimento=data_em(3000), liquidez="NO_VENCIMENTO", investimentoMinimo=999999),
        )
        assert resultado.score == 0

    @pytest.mark.parametrize("score,esperado", [
        (0, "BAIXA"), (49, "BAIXA"), (50, "MEDIA"), (79, "MEDIA"), (80, "ALTA"), (100, "ALTA"),
    ])
    def test_classificacao_deve_usar_alta_a_partir_de_80_e_media_a_partir_de_50(self, score, esperado):
        assert _classificar_compatibilidade(score) == esperado


class TestJustificativa:
    def test_deve_gerar_justificativa_nao_vazia(self):
        resultado = ranquear_um(perfil(), titulo())
        assert resultado.justificativa

    def test_deve_explicar_o_motivo_principal(self):
        resultado = ranquear_um(
            perfil(perfilRisco="CONSERVADOR", horizonte="CURTO_PRAZO"),
            titulo(indexador="SELIC", vencimento=data_em(100)),
        )
        assert resultado.justificativa.startswith("Indexador SELIC é o mais indicado para o perfil conservador")


class TestCriteriosExplicados:
    def test_deve_devolver_os_criterios_com_descricao(self):
        resultado = ranquear_um(
            perfil(perfilRisco="CONSERVADOR", horizonte="CURTO_PRAZO", objetivo="CRESCIMENTO_PATRIMONIO", valorDisponivel=1000),
            titulo(tipo="CDB", indexador="PREFIXADO", vencimento=data_em(3000), liquidez="NO_VENCIMENTO",
                   garantidoFGC=False, investimentoMinimo=5000),
        )
        assert [(c.chave, c.pontos) for c in resultado.criterios] == [
            ("taxa_crescimento", 15), ("indexador_aceitavel", 5), ("vencimento_muito_alem_horizonte", -10),
        ]
        assert resultado.criterios[-1].descricao == "Vence muito longe do prazo em que você pretende usar o dinheiro"

    @pytest.mark.parametrize("risco", ["CONSERVADOR", "MODERADO", "ARROJADO"])
    @pytest.mark.parametrize("horizonte", ["CURTO_PRAZO", "MEDIO_PRAZO", "LONGO_PRAZO"])
    @pytest.mark.parametrize("objetivo", ["RENDA_PASSIVA", "CRESCIMENTO_PATRIMONIO", "PRESERVAR_CAPITAL"])
    def test_todo_criterio_deve_ter_descricao_e_a_soma_deve_explicar_o_score(self, risco, horizonte, objetivo):
        for indexador in ["SELIC", "CDI", "IPCA", "PREFIXADO"]:
            for dias in [100, 1000, 3000]:
                for liquidez in ["DIARIA", "NO_VENCIMENTO"]:
                    perfil_teste = perfil(perfilRisco=risco, horizonte=horizonte, objetivo=objetivo, valorDisponivel=5000)
                    dados = titulo(tipo="TESOURO" if indexador == "SELIC" else "LCI", indexador=indexador,
                                   vencimento=data_em(dias), liquidez=liquidez, isentoIR=dias == 1000,
                                   garantidoFGC=dias != 3000, investimentoMinimo=10 if dias == 100 else 99999)
                    resultado = ranquear_um(perfil_teste, dados)
                    criterios = ranking_service._avaliar_criterios_fixa(ranking_service.AtivoFixoSchema(**dados), perfil_teste)
                    assert set(criterios) <= set(cfg.DESCRICOES_FIXA)
                    soma = sum(c.pontos for c in resultado.criterios)
                    assert max(0, min(100, soma)) == resultado.score

