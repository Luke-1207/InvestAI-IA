from app.models import AtivoVariavelSchema
from app.services.analise_mercado import calcular_dy_vs_media_setorial, calcular_posicao_52_semanas


def ativo(**overrides):
    dados = dict(
        codigo="TAEE3", tipo="ACAO", setor="Energia Elétrica",
        preco=38.42, dy=6.8, variacao30d=5.1,
    )
    dados.update(overrides)
    return AtivoVariavelSchema(**dados)


class TestPosicao52Semanas:
    def test_deve_indicar_proxima_ao_topo(self):
        resultado = calcular_posicao_52_semanas(ativo(preco=41.0, variacao52s={"min": 28.10, "max": 41.90}))
        assert "topo" in resultado

    def test_deve_indicar_proxima_a_base(self):
        resultado = calcular_posicao_52_semanas(ativo(preco=29.0, variacao52s={"min": 28.10, "max": 41.90}))
        assert "base" in resultado

    def test_deve_indicar_meio_da_faixa(self):
        resultado = calcular_posicao_52_semanas(ativo(preco=35.0, variacao52s={"min": 28.10, "max": 41.90}))
        assert "meio" in resultado

    def test_deve_retornar_none_quando_sem_dados_de_52_semanas(self):
        assert calcular_posicao_52_semanas(ativo(variacao52s=None)) is None

    def test_deve_retornar_none_quando_faixa_degenerada(self):
        assert calcular_posicao_52_semanas(ativo(variacao52s={"min": 30, "max": 30})) is None


class TestDyVsMediaSetorial:
    def test_deve_indicar_acima_da_media(self):
        resultado = calcular_dy_vs_media_setorial(ativo(dy=6.8, mediaSetorialDY=5.2))
        assert "acima" in resultado

    def test_deve_indicar_abaixo_da_media(self):
        resultado = calcular_dy_vs_media_setorial(ativo(dy=3.0, mediaSetorialDY=5.2))
        assert "abaixo" in resultado

    def test_deve_indicar_alinhado_quando_diferenca_pequena(self):
        resultado = calcular_dy_vs_media_setorial(ativo(dy=5.2, mediaSetorialDY=5.2))
        assert "alinhado" in resultado

    def test_deve_retornar_none_quando_sem_media_setorial(self):
        assert calcular_dy_vs_media_setorial(ativo(mediaSetorialDY=None)) is None