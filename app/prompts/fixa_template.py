from app.models import AtivoFixoSchema, PerfilSchema

_TEMPLATE = """Você é um assistente de análise de investimentos educacional.
Explique o título de renda fixa abaixo de forma simples para
um investidor iniciante com o perfil descrito. Inclua:
rentabilidade estimada bruta e líquida (considere IR regressivo
se aplicável), para qual perfil o título é mais adequado e
um ponto de atenção. Máximo de 4 frases.

TÍTULO:
- Tipo: {tipo} | Emissor: {emissor}
- Indexador: {indexador} | Taxa: {taxa}%
- Vencimento: {vencimento} | Liquidez: {liquidez}
- Isento IR: {isentoIR} | Garantido FGC: {garantidoFGC}
- Investimento mínimo: R$ {investimentoMinimo}
- Selic atual de referência: {selicAtual}

PERFIL DO INVESTIDOR:
- Risco: {perfilRisco} | Objetivo: {objetivo} | Horizonte: {horizonte}

Responda apenas com o texto do resumo, sem títulos ou marcadores."""


def _fmt(valor, sufixo: str = "") -> str:
    return "não disponível" if valor is None else f"{valor}{sufixo}"


def montar_prompt(ativo: AtivoFixoSchema, perfil: PerfilSchema) -> str:
    emissor = ativo.emissor or ("Tesouro Nacional" if ativo.tipo.value == "TESOURO" else "não informado")

    return _TEMPLATE.format(
        tipo=ativo.tipo.value,
        emissor=emissor,
        indexador=ativo.indexador.value,
        taxa=ativo.taxaPercentual,
        vencimento=ativo.vencimento.isoformat(),
        liquidez=ativo.liquidez.value,
        isentoIR="Sim" if ativo.isentoIR else "Não",
        garantidoFGC="Sim" if ativo.garantidoFGC else "Não",
        investimentoMinimo=ativo.investimentoMinimo,
        selicAtual=_fmt(ativo.selicAtual, "%"),
        perfilRisco=perfil.perfilRisco.value,
        objetivo=perfil.objetivo.value,
        horizonte=perfil.horizonte.value,
    )