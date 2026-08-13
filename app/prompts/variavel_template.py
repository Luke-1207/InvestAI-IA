from app.models import AtivoVariavelSchema, PerfilSchema

_TEMPLATE = """Você é um assistente de análise de investimentos educacional.
Gere um resumo claro e objetivo sobre o ativo abaixo para um
investidor com o perfil descrito. Use linguagem simples, sem
jargão técnico excessivo. Máximo de 4 frases. Não faça previsões
de mercado. Finalize com uma nota de adequação ao perfil.

ATIVO:
- Código: {codigo} | Nome: {nome} | Tipo: {tipo}
- Setor: {setor}
- Preço atual: R$ {preco} | DY: {dy}% | P/L: {pl} | P/VP: {pvp}
- Variação 30 dias: {variacao30d}%
- Mín/Máx 52 semanas: R$ {min52s} / R$ {max52s}
- DY médio do setor: {mediaSetorialDY}

PERFIL DO INVESTIDOR:
- Risco: {perfilRisco} | Objetivo: {objetivo} | Horizonte: {horizonte}

Responda apenas com o texto do resumo, sem títulos ou marcadores."""


def _fmt(valor, sufixo: str = "") -> str:
    return "não disponível" if valor is None else f"{valor}{sufixo}"


def montar_prompt(ativo: AtivoVariavelSchema, perfil: PerfilSchema) -> str:
    min52s = ativo.variacao52s.min if ativo.variacao52s else None
    max52s = ativo.variacao52s.max if ativo.variacao52s else None

    return _TEMPLATE.format(
        codigo=ativo.codigo,
        nome=ativo.nome or ativo.codigo,
        tipo=ativo.tipo.value,
        setor=ativo.setor,
        preco=ativo.preco,
        dy=ativo.dy,
        pl=_fmt(ativo.pl, "x"),
        pvp=_fmt(ativo.pvp, "x"),
        variacao30d=ativo.variacao30d,
        min52s=_fmt(min52s),
        max52s=_fmt(max52s),
        mediaSetorialDY=_fmt(ativo.mediaSetorialDY, "%"),
        perfilRisco=perfil.perfilRisco.value,
        objetivo=perfil.objetivo.value,
        horizonte=perfil.horizonte.value,
    )