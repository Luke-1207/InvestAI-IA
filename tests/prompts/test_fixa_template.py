from datetime import date

from app.models import AtivoFixoSchema, PerfilSchema
from app.prompts import fixa_template


def perfil():
    return PerfilSchema(
        perfilRisco="CONSERVADOR", horizonte="CURTO_PRAZO",
        objetivo="PRESERVAR_CAPITAL", valorDisponivel=1000.0,
    )


def test_montar_prompt_deve_incluir_dados_completos_do_titulo():
    ativo = AtivoFixoSchema(
        codigo="TESOURO_SELIC_2029", tipo="TESOURO", indexador="SELIC",
        taxaPercentual=100.0, vencimento=date(2029, 1, 1),
        investimentoMinimo=30.0, liquidez="DIARIA",
        garantidoFGC=False, isentoIR=False, selicAtual=13.75,
    )

    prompt = fixa_template.montar_prompt(ativo, perfil())

    assert "TESOURO" in prompt
    assert "SELIC" in prompt
    assert "13.75%" in prompt
    assert "Tesouro Nacional" in prompt


def test_montar_prompt_deve_lidar_com_selic_ausente():
    ativo = AtivoFixoSchema(
        codigo="CDB_BANCO_X", tipo="CDB", indexador="CDI",
        taxaPercentual=110.0, vencimento=date(2027, 6, 1),
        investimentoMinimo=500.0, liquidez="NO_VENCIMENTO",
        garantidoFGC=True, isentoIR=False,
    )

    prompt = fixa_template.montar_prompt(ativo, perfil())

    assert "não disponível" in prompt