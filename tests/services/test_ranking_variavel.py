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


class TestFiltroTipoAceitoEliminatorio:
    def test_deve_excluir_ativo_cujo_tipo_nao_esta_em_tiposAceitos(self):
        assert ranquear_um(perfil(tiposAceitos=["FII"]), ativo(tipo="ACAO")) is None

    def test_deve_incluir_ativo_cujo_tipo_esta_em_tiposAceitos(self):
        assert ranquear_um(perfil(tiposAceitos=["ACAO"]), ativo(tipo="ACAO")) is not None

    def test_deve_incluir_todos_quando_tiposAceitos_vazio(self):
        assert ranquear_um(perfil(tiposAceitos=[]), ativo(tipo="ETF")) is not None


class TestVolatilidadeXPerfilRisco:
    @pytest.mark.parametrize("risco,volatilidade,neutra", [
        ("CONSERVADOR", "BAIXA", "MEDIA"),
        ("MODERADO", "MEDIA", "BAIXA"),
        ("ARROJADO", "ALTA", "MEDIA"),
    ])
    def test_combinacao_favoravel_deve_pontuar_mais_que_neutra(self, risco, volatilidade, neutra):
        favoravel = ranquear_um(perfil(perfilRisco=risco), ativo(volatilidade=volatilidade, dy=0, preco=999999))
        neutro = ranquear_um(perfil(perfilRisco=risco), ativo(volatilidade=neutra, dy=0, preco=999999))
        assert favoravel.score > neutro.score

    def test_conservador_com_alta_volatilidade_deve_penalizar_score(self):
        desfavoravel = ranquear_um(perfil(perfilRisco="CONSERVADOR"), ativo(volatilidade="ALTA", dy=0, preco=999999))
        neutro = ranquear_um(perfil(perfilRisco="CONSERVADOR"), ativo(volatilidade="MEDIA", dy=0, preco=999999))
        assert desfavoravel.score < neutro.score


class TestDyXObjetivo:
    def test_renda_passiva_com_dy_alto_deve_pontuar_mais(self):
        alto = ranquear_um(perfil(objetivo="RENDA_PASSIVA"), ativo(dy=8.0, volatilidade=None, preco=999999))
        baixo = ranquear_um(perfil(objetivo="RENDA_PASSIVA"), ativo(dy=1.0, volatilidade=None, preco=999999))
        assert alto.score > baixo.score

    def test_crescimento_patrimonio_com_dy_baixo_deve_pontuar_mais(self):
        baixo = ranquear_um(
            perfil(objetivo="CRESCIMENTO_PATRIMONIO", horizonte="CURTO_PRAZO"),
            ativo(dy=1.0, volatilidade=None, preco=999999),
        )
        alto = ranquear_um(
            perfil(objetivo="CRESCIMENTO_PATRIMONIO", horizonte="CURTO_PRAZO"),
            ativo(dy=8.0, volatilidade=None, preco=999999),
        )
        assert baixo.score > alto.score


class TestPrecoXValorDisponivel:
    def test_preco_dentro_do_valor_disponivel_deve_pontuar_mais(self):
        dentro = ranquear_um(perfil(valorDisponivel=100), ativo(preco=50, dy=0, volatilidade=None))
        fora = ranquear_um(perfil(valorDisponivel=100), ativo(preco=500, dy=0, volatilidade=None))
        assert dentro.score > fora.score

    def test_preco_igual_ao_valor_disponivel_deve_pontuar(self):
        igual = ranquear_um(perfil(valorDisponivel=100), ativo(preco=100, dy=0, volatilidade=None))
        acima = ranquear_um(perfil(valorDisponivel=100), ativo(preco=100.01, dy=0, volatilidade=None))
        assert igual.score > acima.score


class TestSetorPreferidoEvitado:
    def test_setor_preferido_deve_aumentar_score(self):
        preferido = ranquear_um(
            perfil(setoresPreferidos=[{"setor": "Energia Elétrica", "preferencia": "PREFERIR"}]),
            ativo(setor="Energia Elétrica", dy=0, volatilidade=None, preco=999999),
        )
        neutro = ranquear_um(perfil(), ativo(setor="Energia Elétrica", dy=0, volatilidade=None, preco=999999))
        assert preferido.score > neutro.score

    def test_setor_evitado_deve_diminuir_score(self):
        evitado = ranquear_um(
            perfil(setoresPreferidos=[{"setor": "Energia Elétrica", "preferencia": "EVITAR"}]),
            ativo(setor="Energia Elétrica", dy=0, volatilidade=None, preco=999999),
        )
        neutro = ranquear_um(perfil(), ativo(setor="Energia Elétrica", dy=0, volatilidade=None, preco=999999))
        assert evitado.score < neutro.score

    def test_comparacao_de_setor_deve_ser_case_insensitive(self):
        preferido = ranquear_um(
            perfil(setoresPreferidos=[{"setor": "energia elétrica", "preferencia": "PREFERIR"}]),
            ativo(setor="Energia Elétrica", dy=0, volatilidade=None, preco=999999),
        )
        neutro = ranquear_um(perfil(), ativo(setor="Energia Elétrica", dy=0, volatilidade=None, preco=999999))
        assert preferido.score > neutro.score


class TestHorizonteXTipoDeAtivo:
    def test_longo_prazo_com_dy_baixo_deve_pontuar_mais_que_curto_prazo(self):
        longo = ranquear_um(
            perfil(horizonte="LONGO_PRAZO", objetivo="CRESCIMENTO_PATRIMONIO"),
            ativo(dy=1.0, volatilidade=None, preco=999999),
        )
        curto = ranquear_um(
            perfil(horizonte="CURTO_PRAZO", objetivo="CRESCIMENTO_PATRIMONIO"),
            ativo(dy=1.0, volatilidade=None, preco=999999),
        )
        assert longo.score > curto.score


class TestNormalizacaoEClassificacao:
    def test_score_nunca_deve_ser_negativo(self):
        resultado = ranquear_um(
            perfil(perfilRisco="CONSERVADOR", setoresPreferidos=[{"setor": "Petróleo", "preferencia": "EVITAR"}]),
            ativo(setor="Petróleo", volatilidade="ALTA", dy=0, preco=999999),
        )
        assert resultado.score >= 0

    def test_score_nunca_deve_exceder_100(self):
        resultado = ranquear_um(
            perfil(
                perfilRisco="CONSERVADOR", horizonte="LONGO_PRAZO", objetivo="RENDA_PASSIVA",
                valorDisponivel=999999, tiposAceitos=["ACAO"],
                setoresPreferidos=[{"setor": "Energia Elétrica", "preferencia": "PREFERIR"}],
            ),
            ativo(tipo="ACAO", setor="Energia Elétrica", volatilidade="BAIXA", dy=8.0, preco=10),
        )
        assert resultado.score <= 100

    @pytest.mark.parametrize("score,esperado", [
        (0, "BAIXA"), (39, "BAIXA"), (40, "MEDIA"), (69, "MEDIA"), (70, "ALTA"), (100, "ALTA"),
    ])
    def test_classificacao_deve_respeitar_limiares(self, score, esperado):
        assert _classificar_compatibilidade(score) == esperado


class TestJustificativa:
    def test_deve_gerar_justificativa_nao_vazia(self):
        resultado = ranquear_um(perfil(), ativo())
        assert resultado.justificativa

    def test_ativo_sem_nenhum_criterio_positivo_deve_ter_justificativa_generica(self):
        resultado = ranquear_um(
            perfil(perfilRisco="ARROJADO", objetivo="PRESERVAR_CAPITAL", valorDisponivel=1, tiposAceitos=["FII"]),
            ativo(tipo="FII", volatilidade="BAIXA", dy=5.0, preco=999999),
        )
        assert resultado.justificativa


class TestRendaFixaAindaEhStub:
    def test_modulo_fixa_deve_continuar_usando_stub_temporario(self):
        request = RankingRequestSchema(
            correlationId=CORRELATION_ID, modulo="FIXA", perfil=perfil(),
            ativos=[{
                "codigo": "TESOURO_SELIC_2029", "tipo": "TESOURO", "indexador": "SELIC",
                "taxaPercentual": 100.0, "vencimento": "2029-01-01",
                "investimentoMinimo": 30.0, "liquidez": "DIARIA",
            }],
        )
        response = ranking_service.ranquear(request)
        assert response.ativos[0].score == 50
        assert response.ativos[0].compatibilidade == "MEDIA"