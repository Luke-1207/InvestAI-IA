from typing import Union

from app.models import AtivoFixoSchema, AtivoVariavelSchema, PerfilSchema

_TEMPLATE = """Você é um assistente de análise de investimentos educacional.
Compare os dois ativos abaixo para um investidor com o perfil descrito.
Aponte as principais diferenças relevantes (risco, liquidez, potencial de
retorno) e diga qual deles tende a se encaixar melhor no perfil informado,
com uma justificativa breve. Os dois ativos podem ser de categorias
diferentes (por exemplo, uma ação e um título de renda fixa) — nesse caso,
compare pelo que for comparável (risco, liquidez, horizonte), sem forçar
uma métrica que só faz sentido pra um dos dois. Máximo de 5 frases.

ATIVO A ({codigoA}):
{descricaoA}

ATIVO B ({codigoB}):
{descricaoB}

PERFIL DO INVESTIDOR:
- Risco: {perfilRisco} | Objetivo: {objetivo} | Horizonte: {horizonte}

Responda apenas com o texto do veredito, sem títulos ou marcadores."""


def _descrever_ativo(ativo: Union[AtivoVariavelSchema, AtivoFixoSchema]) -> str:
    if isinstance(ativo, AtivoFixoSchema):
        emissor = ativo.emissor or ("Tesouro Nacional" if ativo.tipo.value == "TESOURO" else "não informado")
        return (
            f"Título de renda fixa — Tipo: {ativo.tipo.value} | Emissor: {emissor} | "
            f"Indexador: {ativo.indexador.value} | Taxa: {ativo.taxaPercentual}% | "
            f"Vencimento: {ativo.vencimento.isoformat()} | Liquidez: {ativo.liquidez.value} | "
            f"Isento IR: {'Sim' if ativo.isentoIR else 'Não'} | "
            f"Investimento mínimo: R$ {ativo.investimentoMinimo}"
        )
    return (
        f"Ativo de renda variável ({ativo.tipo.value}) — Setor: {ativo.setor} | "
        f"Preço: R$ {ativo.preco} | Dividend Yield: {ativo.dy}% | "
        f"Variação nos últimos 30 dias: {ativo.variacao30d}%"
    )


def montar_prompt(
    ativo_a: Union[AtivoVariavelSchema, AtivoFixoSchema],
    ativo_b: Union[AtivoVariavelSchema, AtivoFixoSchema],
    perfil: PerfilSchema,
) -> str:
    return _TEMPLATE.format(
        codigoA=ativo_a.codigo,
        descricaoA=_descrever_ativo(ativo_a),
        codigoB=ativo_b.codigo,
        descricaoB=_descrever_ativo(ativo_b),
        perfilRisco=perfil.perfilRisco.value,
        objetivo=perfil.objetivo.value,
        horizonte=perfil.horizonte.value,
    )