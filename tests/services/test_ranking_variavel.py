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


def ativo(**overrides):
    dados = dict(
        codigo="TAEE3", tipo="ACAO", setor="Energia Elétrica",
        preco=38.42, dy=6.8, variacao30d=1.0, volatilidade="BAIXA",
    )
    dados.update(overrides)
    return dados


def ranquear_um(perfil_schema, ativo_dict):
    request = RankingRequestSchema(
        correlationId=CORRELATION_ID, modulo="VARIAVEL", perfil=perfil_schema, ativos=[ativo_dict],
    )
    response = ranking_service.ranquear(request)
    return response.ativos[0] if response.ativos else None


def preferir(setor):
    return [{"setor": setor, "preferencia": "PREFERIR"}]


def evitar(setor):
    return [{"setor": setor, "preferencia": "EVITAR"}]


class TestPesos:
    def test_soma_dos_melhores_criterios_deve_fechar_100(self):
        p = cfg.PESOS
        maximo = p["volatilidade_ideal"] + p["dy_alinhado"] + p["horizonte_longo"] + p["preco_acessivel"] + p["setor_preferido"]
        assert maximo == 100

    def test_tipo_aceito_nao_deve_mais_pontuar_porque_o_filtro_ja_eliminou_os_outros(self):
        assert "tipo_aceito" not in cfg.PESOS


class TestCenariosIguaisAoJava:
    """Mesmos cenários de AcaoPontuacaoServiceTest, para garantir que os dois motores dão a mesma leitura."""

    def test_acao_ideal_para_o_perfil_deve_chegar_a_100(self):
        resultado = ranquear_um(
            perfil(perfilRisco="ARROJADO", horizonte="LONGO_PRAZO", objetivo="CRESCIMENTO_PATRIMONIO",
                   valorDisponivel=9999, setoresPreferidos=preferir("Energia")),
            ativo(setor="Energia", preco=10, volatilidade="ALTA", dy=1),
        )
        assert resultado.score == 100
        assert resultado.compatibilidade == "ALTA"

    def test_quem_nao_escolheu_setores_ainda_deve_conseguir_alta(self):
        resultado = ranquear_um(
            perfil(perfilRisco="MODERADO", horizonte="LONGO_PRAZO", objetivo="CRESCIMENTO_PATRIMONIO", valorDisponivel=9999),
            ativo(setor="Energia", preco=10, volatilidade="MEDIA", dy=1),
        )
        assert resultado.score == 93
        assert resultado.compatibilidade == "ALTA"

    def test_preservar_capital_com_dividendos(self):
        resultado = ranquear_um(
            perfil(perfilRisco="CONSERVADOR", horizonte="LONGO_PRAZO", objetivo="PRESERVAR_CAPITAL", valorDisponivel=9999),
            ativo(setor="Energia", preco=10, volatilidade="BAIXA", dy=7),
        )
        assert resultado.score == 93
        assert "Oscilação de preço compatível" in resultado.justificativa

    def test_combinacao_parcial_deve_ficar_em_media(self):
        resultado = ranquear_um(
            perfil(perfilRisco="MODERADO", horizonte="MEDIO_PRAZO", objetivo="RENDA_PASSIVA", valorDisponivel=9999),
            ativo(setor="Energia", preco=10, volatilidade="BAIXA", dy=4),
        )
        assert resultado.score == 53
        assert resultado.compatibilidade == "MEDIA"

    def test_acao_oposta_ao_perfil_e_em_setor_evitado_deve_ficar_em_zero(self):
        resultado = ranquear_um(
            perfil(perfilRisco="CONSERVADOR", horizonte="CURTO_PRAZO", objetivo="RENDA_PASSIVA",
                   valorDisponivel=5, setoresPreferidos=evitar("Energia")),
            ativo(setor="Energia", preco=10, volatilidade="ALTA", dy=1),
        )
        assert resultado.score == 0
        assert resultado.compatibilidade == "BAIXA"
        assert "prefere evitar" in resultado.justificativa
        assert "Oscila mais" in resultado.justificativa

    def test_arrojado_com_acao_que_quase_nao_oscila(self):
        resultado = ranquear_um(
            perfil(perfilRisco="ARROJADO", horizonte="LONGO_PRAZO", objetivo="CRESCIMENTO_PATRIMONIO", valorDisponivel=9999),
            ativo(setor="Energia", preco=10, volatilidade="BAIXA", dy=1),
        )
        assert resultado.score == 48


class TestFiltroTipoAceitoEliminatorio:
    def test_deve_excluir_ativo_cujo_tipo_nao_esta_em_tiposAceitos(self):
        assert ranquear_um(perfil(tiposAceitos=["FII"]), ativo(tipo="ACAO")) is None

    def test_deve_incluir_ativo_cujo_tipo_esta_em_tiposAceitos(self):
        assert ranquear_um(perfil(tiposAceitos=["ACAO"]), ativo(tipo="ACAO")) is not None

    def test_deve_incluir_todos_quando_tiposAceitos_vazio(self):
        assert ranquear_um(perfil(tiposAceitos=[]), ativo(tipo="ETF")) is not None


class TestVolatilidadeXPerfilRisco:
    @pytest.mark.parametrize("risco,ideal,vizinha", [
        ("CONSERVADOR", "BAIXA", "MEDIA"),
        ("MODERADO", "MEDIA", "BAIXA"),
        ("ARROJADO", "ALTA", "MEDIA"),
    ])
    def test_volatilidade_ideal_deve_pontuar_mais_que_a_vizinha(self, risco, ideal, vizinha):
        favoravel = ranquear_um(perfil(perfilRisco=risco), ativo(volatilidade=ideal, dy=0, preco=999999))
        proxima = ranquear_um(perfil(perfilRisco=risco), ativo(volatilidade=vizinha, dy=0, preco=999999))
        assert favoravel.score - proxima.score == 20

    def test_conservador_com_alta_volatilidade_deve_penalizar_score(self):
        oposta = ranquear_um(perfil(perfilRisco="CONSERVADOR"), ativo(volatilidade="ALTA", dy=0, preco=999999))
        proxima = ranquear_um(perfil(perfilRisco="CONSERVADOR"), ativo(volatilidade="MEDIA", dy=0, preco=999999))
        assert oposta.score < proxima.score

    def test_sem_volatilidade_informada_deve_tratar_como_media_igual_ao_java(self):
        sem = ranquear_um(perfil(perfilRisco="MODERADO"), ativo(volatilidade=None, dy=0, preco=999999))
        media = ranquear_um(perfil(perfilRisco="MODERADO"), ativo(volatilidade="MEDIA", dy=0, preco=999999))
        assert sem.score == media.score


class TestDyXObjetivo:
    @pytest.mark.parametrize("dy,pontos_esperados", [(8.0, 25), (4.0, 12), (1.0, 0)])
    def test_renda_passiva_deve_valorizar_dividendos_em_faixas(self, dy, pontos_esperados):
        base = ranquear_um(perfil(objetivo="RENDA_PASSIVA"), ativo(dy=1.0, preco=999999))
        resultado = ranquear_um(perfil(objetivo="RENDA_PASSIVA"), ativo(dy=dy, preco=999999))
        assert resultado.score - base.score == pontos_esperados

    def test_crescimento_patrimonio_com_dy_baixo_deve_pontuar_mais(self):
        baixo = ranquear_um(perfil(objetivo="CRESCIMENTO_PATRIMONIO"), ativo(dy=1.0, preco=999999))
        alto = ranquear_um(perfil(objetivo="CRESCIMENTO_PATRIMONIO"), ativo(dy=8.0, preco=999999))
        assert baixo.score - alto.score == 20

    def test_preservar_capital_deve_valorizar_empresas_que_pagam_dividendos(self):
        paga = ranquear_um(perfil(objetivo="PRESERVAR_CAPITAL"), ativo(dy=4.0, preco=999999))
        nao_paga = ranquear_um(perfil(objetivo="PRESERVAR_CAPITAL"), ativo(dy=1.0, preco=999999))
        assert paga.score - nao_paga.score == 20


class TestHorizonte:
    def test_longo_prazo_deve_pontuar_mais_que_medio_e_medio_mais_que_curto(self):
        longo = ranquear_um(perfil(horizonte="LONGO_PRAZO"), ativo(preco=999999))
        medio = ranquear_um(perfil(horizonte="MEDIO_PRAZO"), ativo(preco=999999))
        curto = ranquear_um(perfil(horizonte="CURTO_PRAZO"), ativo(preco=999999))
        assert (longo.score - medio.score, medio.score - curto.score) == (7, 8)


class TestPrecoXValorDisponivel:
    def test_preco_dentro_do_valor_disponivel_deve_pontuar_mais(self):
        dentro = ranquear_um(perfil(valorDisponivel=100), ativo(preco=50, dy=0))
        fora = ranquear_um(perfil(valorDisponivel=100), ativo(preco=500, dy=0))
        assert dentro.score - fora.score == 10

    def test_preco_igual_ao_valor_disponivel_deve_pontuar(self):
        igual = ranquear_um(perfil(valorDisponivel=100), ativo(preco=100, dy=0))
        acima = ranquear_um(perfil(valorDisponivel=100), ativo(preco=100.01, dy=0))
        assert igual.score > acima.score


class TestSetorPreferidoEvitado:
    def test_setor_preferido_deve_somar_mais_que_setor_neutro(self):
        preferido = ranquear_um(perfil(setoresPreferidos=preferir("Energia Elétrica")), ativo(dy=0, preco=999999))
        neutro = ranquear_um(perfil(), ativo(dy=0, preco=999999))
        assert preferido.score - neutro.score == 7

    def test_setor_evitado_deve_diminuir_score(self):
        evitado = ranquear_um(perfil(setoresPreferidos=evitar("Energia Elétrica")), ativo(dy=0, preco=999999))
        neutro = ranquear_um(perfil(), ativo(dy=0, preco=999999))
        assert neutro.score - evitado.score == 28

    def test_comparacao_de_setor_deve_ser_case_insensitive(self):
        preferido = ranquear_um(perfil(setoresPreferidos=preferir("energia elétrica")), ativo(dy=0, preco=999999))
        neutro = ranquear_um(perfil(), ativo(dy=0, preco=999999))
        assert preferido.score > neutro.score


class TestNormalizacaoEClassificacao:
    def test_score_nunca_deve_ser_negativo(self):
        resultado = ranquear_um(
            perfil(perfilRisco="CONSERVADOR", setoresPreferidos=evitar("Petróleo")),
            ativo(setor="Petróleo", volatilidade="ALTA", dy=0, preco=999999),
        )
        assert resultado.score == 0

    @pytest.mark.parametrize("score,esperado", [
        (0, "BAIXA"), (49, "BAIXA"), (50, "MEDIA"), (79, "MEDIA"), (80, "ALTA"), (100, "ALTA"),
    ])
    def test_classificacao_deve_usar_alta_a_partir_de_80_e_media_a_partir_de_50(self, score, esperado):
        assert _classificar_compatibilidade(score) == esperado


class TestJustificativa:
    def test_deve_gerar_justificativa_nao_vazia(self):
        resultado = ranquear_um(perfil(), ativo())
        assert resultado.justificativa

    def test_setor_neutro_e_dy_fraco_nao_devem_virar_frase(self):
        resultado = ranquear_um(
            perfil(perfilRisco="ARROJADO", horizonte="CURTO_PRAZO", objetivo="CRESCIMENTO_PATRIMONIO", valorDisponivel=1),
            ativo(volatilidade="MEDIA", dy=8.0, preco=999999),
        )
        assert resultado.justificativa == "Oscilação de preço aceitável para o seu perfil de risco."


class TestCriteriosExplicados:
    def test_deve_devolver_os_criterios_do_que_somou_ao_que_tirou(self):
        resultado = ranquear_um(
            perfil(perfilRisco="CONSERVADOR", horizonte="LONGO_PRAZO", objetivo="RENDA_PASSIVA",
                   valorDisponivel=9999, setoresPreferidos=evitar("Energia")),
            ativo(setor="Energia", preco=10, volatilidade="ALTA", dy=7),
        )
        assert [(c.chave, c.pontos) for c in resultado.criterios] == [
            ("dy_renda_passiva", 25), ("horizonte_longo", 15), ("preco_acessivel", 10),
            ("volatilidade_alta_demais", -10), ("setor_evitado", -20),
        ]
        assert all(c.descricao for c in resultado.criterios)

    @pytest.mark.parametrize("risco", ["CONSERVADOR", "MODERADO", "ARROJADO"])
    @pytest.mark.parametrize("horizonte", ["CURTO_PRAZO", "MEDIO_PRAZO", "LONGO_PRAZO"])
    @pytest.mark.parametrize("objetivo", ["RENDA_PASSIVA", "CRESCIMENTO_PATRIMONIO", "PRESERVAR_CAPITAL"])
    def test_todo_criterio_deve_ter_descricao_e_a_soma_deve_explicar_o_score(self, risco, horizonte, objetivo):
        for volatilidade in ["BAIXA", "MEDIA", "ALTA"]:
            for dy in [1.0, 4.0, 8.0]:
                for setor in ["Energia", "Bancos", "Varejo"]:
                    perfil_teste = perfil(
                        perfilRisco=risco, horizonte=horizonte, objetivo=objetivo, valorDisponivel=50,
                        setoresPreferidos=preferir("Energia") + evitar("Bancos"),
                    )
                    resultado = ranquear_um(perfil_teste, ativo(setor=setor, volatilidade=volatilidade, dy=dy, preco=40))
                    criterios = ranking_service._avaliar_criterios(
                        ranking_service.AtivoVariavelSchema(**ativo(setor=setor, volatilidade=volatilidade, dy=dy, preco=40)),
                        perfil_teste,
                    )
                    assert set(criterios) <= set(cfg.DESCRICOES_VARIAVEL)
                    soma = sum(c.pontos for c in resultado.criterios)
                    assert max(0, min(100, soma)) == resultado.score

