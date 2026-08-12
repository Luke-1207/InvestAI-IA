import pytest
from pydantic import ValidationError

from app.models.enums import (
    HorizonteInvestimento,
    ObjetivoFinanceiro,
    PerfilRisco,
    TipoAtivoVariavel,
)
from app.models.perfil import PerfilSchema, SetorPreferidoSchema


def perfil_valido(**overrides):
    dados = dict(
        perfilRisco=PerfilRisco.MODERADO,
        horizonte=HorizonteInvestimento.LONGO_PRAZO,
        objetivo=ObjetivoFinanceiro.RENDA_PASSIVA,
        valorDisponivel=5000.0,
        tiposAceitos=[TipoAtivoVariavel.ACAO, TipoAtivoVariavel.FII],
        setoresPreferidos=[{"setor": "Energia", "preferencia": "PREFERIR"}],
    )
    dados.update(overrides)
    return dados


def test_perfil_schema_deve_aceitar_dados_validos():
    perfil = PerfilSchema(**perfil_valido())

    assert perfil.perfilRisco == PerfilRisco.MODERADO
    assert perfil.valorDisponivel == 5000.0
    assert perfil.setoresPreferidos[0].setor == "Energia"


def test_perfil_schema_deve_aceitar_listas_vazias_por_padrao():
    perfil = PerfilSchema(**perfil_valido(tiposAceitos=[], setoresPreferidos=[]))

    assert perfil.tiposAceitos == []
    assert perfil.setoresPreferidos == []


def test_perfil_schema_deve_rejeitar_perfil_risco_invalido():
    with pytest.raises(ValidationError):
        PerfilSchema(**perfil_valido(perfilRisco="ARRISCADO"))


def test_perfil_schema_deve_rejeitar_valor_disponivel_zero_ou_negativo():
    with pytest.raises(ValidationError):
        PerfilSchema(**perfil_valido(valorDisponivel=0))
    with pytest.raises(ValidationError):
        PerfilSchema(**perfil_valido(valorDisponivel=-100))


def test_perfil_schema_deve_rejeitar_campo_obrigatorio_ausente():
    dados = perfil_valido()
    del dados["objetivo"]

    with pytest.raises(ValidationError):
        PerfilSchema(**dados)


def test_setor_preferido_schema_deve_rejeitar_preferencia_invalida():
    with pytest.raises(ValidationError):
        SetorPreferidoSchema(setor="Tecnologia", preferencia="TALVEZ")