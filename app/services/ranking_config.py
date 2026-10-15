from app.models.enums import HorizonteInvestimento, Indexador, PerfilRisco, Volatilidade

# Os pesos abaixo precisam ser iguais aos do Java (AcaoPontuacaoService e RendaFixaPontuacaoService).
# Em cada dimensão o melhor caso soma: renda variável 35 + 25 + 15 + 10 + 15 = 100,
# renda fixa 30 + 25 + 15 + 15 + 10 + 5 = 100.

SCORE_MINIMO = 0
SCORE_MAXIMO = 100
LIMIAR_ALTA = 80
LIMIAR_MEDIA = 50

PESOS = {
    "volatilidade_ideal": 35,
    "volatilidade_proxima": 15,
    "volatilidade_oposta": -10,
    "dy_alinhado": 25,
    "dy_parcial": 12,
    "dy_fraco": 5,
    "horizonte_longo": 15,
    "horizonte_medio": 8,
    "preco_acessivel": 10,
    "setor_preferido": 15,
    "setor_neutro": 8,
    "setor_evitado": -20,
}

DY_ALTO = 6.0
DY_BAIXO = 3.0

ORDEM_RISCO = [PerfilRisco.CONSERVADOR, PerfilRisco.MODERADO, PerfilRisco.ARROJADO]
ORDEM_VOLATILIDADE = [Volatilidade.BAIXA, Volatilidade.MEDIA, Volatilidade.ALTA]

PESOS_FIXA = {
    "indexador_ideal": 30,
    "vencimento_no_horizonte": 25,
    "vencimento_proximo_horizonte": 10,
    "vencimento_muito_alem_horizonte": -10,
    "liquidez_adequada": 15,
    "liquidez_parcial": 8,
    "objetivo_alinhado": 15,
    "objetivo_pos_fixado_preservar": 10,
    "objetivo_parcial": 8,
    "objetivo_fraco": 5,
    "investimento_acessivel": 10,
    "garantia": 5,
}

PESO_INDEXADOR = {
    PerfilRisco.CONSERVADOR: {Indexador.SELIC: 30, Indexador.CDI: 30, Indexador.IPCA: 15, Indexador.PREFIXADO: 5},
    PerfilRisco.MODERADO: {Indexador.SELIC: 20, Indexador.CDI: 20, Indexador.IPCA: 30, Indexador.PREFIXADO: 20},
    PerfilRisco.ARROJADO: {Indexador.SELIC: 10, Indexador.CDI: 10, Indexador.IPCA: 25, Indexador.PREFIXADO: 30},
}

INDEXADORES_POS_FIXADOS = {Indexador.SELIC, Indexador.CDI}

DIAS_LIMITE_CURTO_PRAZO = 365
DIAS_LIMITE_MEDIO_PRAZO = 1825

HORIZONTE_ORDEM = [
    HorizonteInvestimento.CURTO_PRAZO,
    HorizonteInvestimento.MEDIO_PRAZO,
    HorizonteInvestimento.LONGO_PRAZO,
]
