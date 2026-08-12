from datetime import date

import pytest
from pydantic import ValidationError

from app.models.ativo import AtivoFixoSchema, AtivoVariavelSchema
from app.models.enums import Indexador, Liquidez, TipoAtivoFixo, TipoAtivoVariavel


def ativo_variavel_ranking_valido(**overrides):
    dados = dict(
        codigo="TAEE3",
        tipo=TipoAtivoVariavel.ACAO,
        setor="Energia Elétrica",
        preco=38.42,
        dy=6.8,
        variacao30d=5.1,
        volatilidade="BAIXA",
    )
    dados.update(overrides)
    return dados


def ativo_variavel_resumo_valido(**overrides):
    dados = dict(
        codigo="TAEE3",
        nome="Taesa",
        tipo=TipoAtivoVariavel.ACAO,
        setor="Energia Elétrica",
        preco=38.42,
        dy=6.8,
        variacao30d=5.1,
        pl=12.4,
        pvp=1.3,
        variacao52s={"min": 28.10, "max": 41.90},
        mediaSetorialDY=5.2,
    )
    dados.update(overrides)
    return dados


def ativo_fixo_valido(**overrides):
    dados = dict(
        codigo="TESOURO_SELIC_2029",
        tipo=TipoAtivoFixo.TESOURO,
        indexador=Indexador.SELIC,
        taxaPercentual=100.0,
        vencimento=date(2029, 1, 1),
        investimentoMinimo=30.0,
        liquidez=Liquidez.DIARIA,
    )
    dados.update(overrides)
    return dados


def test_ativo_variavel_schema_aceita_payload_de_ranqueamento():
    ativo = AtivoVariavelSchema(**ativo_variavel_ranking_valido())

    assert ativo.codigo == "TAEE3"
    assert ativo.volatilidade == "BAIXA"
    assert ativo.pl is None


def test_ativo_variavel_schema_aceita_payload_de_resumo():
    ativo = AtivoVariavelSchema(**ativo_variavel_resumo_valido())

    assert ativo.nome == "Taesa"
    assert ativo.pl == 12.4
    assert ativo.variacao52s.min == 28.10
    assert ativo.variacao52s.max == 41.90
    assert ativo.volatilidade is None


def test_ativo_variavel_schema_rejeita_preco_zero_ou_negativo():
    with pytest.raises(ValidationError):
        AtivoVariavelSchema(**ativo_variavel_ranking_valido(preco=0))


def test_ativo_variavel_schema_rejeita_dy_negativo():
    with pytest.raises(ValidationError):
        AtivoVariavelSchema(**ativo_variavel_ranking_valido(dy=-1))


def test_ativo_variavel_schema_rejeita_tipo_invalido():
    with pytest.raises(ValidationError):
        AtivoVariavelSchema(**ativo_variavel_ranking_valido(tipo="CRIPTO"))


def test_ativo_fixo_schema_aceita_dados_validos():
    ativo = AtivoFixoSchema(**ativo_fixo_valido())

    assert ativo.tipo == TipoAtivoFixo.TESOURO
    assert ativo.indexador == Indexador.SELIC
    assert ativo.vencimento == date(2029, 1, 1)


def test_ativo_fixo_schema_rejeita_taxa_zero_ou_negativa():
    with pytest.raises(ValidationError):
        AtivoFixoSchema(**ativo_fixo_valido(taxaPercentual=0))


def test_ativo_fixo_schema_rejeita_investimento_minimo_negativo():
    with pytest.raises(ValidationError):
        AtivoFixoSchema(**ativo_fixo_valido(investimentoMinimo=-10))


def test_ativo_fixo_schema_rejeita_liquidez_invalida():
    with pytest.raises(ValidationError):
        AtivoFixoSchema(**ativo_fixo_valido(liquidez="SEMANAL"))