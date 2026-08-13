GLOSSARIO_RENDA_VARIAVEL = {
    "Dividend Yield (DY)": (
        "% dos dividendos pagos em relação ao preço atual. DY de 7% = a cada R$ 100 "
        "investidos, você recebeu R$ 7 em dividendos no último ano. Quanto maior, mais "
        "a ação distribui lucro."
    ),
    "P/L": (
        "Quantos anos levaria para recuperar o investimento só com o lucro da empresa. "
        "P/L 12 = empresa lucrativa, avaliada a 12x seu lucro anual. Muito alto pode "
        "indicar preço esticado."
    ),
    "P/VP": (
        "Preço em relação ao patrimônio líquido por ação. P/VP abaixo de 1 pode indicar "
        "ação \"barata\" em relação aos ativos da empresa."
    ),
    "Mín/Máx 52 semanas": (
        "Faixa de preço do último ano. Mostra se o preço atual está perto do topo ou "
        "da base histórica recente."
    ),
    "Volume": (
        "Quantidade negociada no dia. Alto volume = liquidez, fácil de comprar e vender. "
        "Baixo volume = risco de não conseguir vender na hora que precisar."
    ),
}


def formatar_glossario() -> str:
    return "\n".join(f"- {termo}: {explicacao}" for termo, explicacao in GLOSSARIO_RENDA_VARIAVEL.items())