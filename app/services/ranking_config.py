from app.models.enums import PerfilRisco, Volatilidade
from app.models.enums import HorizonteInvestimento, Indexador, ObjetivoFinanceiro, PerfilRisco

PESOS = {
    "tipo_aceito": 20,
    "volatilidade_favoravel": 20,
    "volatilidade_desfavoravel": -30,
    "dy_renda_passiva": 15,
    "dy_crescimento": 10,
    "preco_acessivel": 10,
    "setor_preferido": 15,
    "setor_evitado": -20,
    "horizonte_longo_crescimento": 10,
}

DY_MINIMO_RENDA_PASSIVA = 6.0
DY_MAXIMO_CRESCIMENTO = 3.0

VOLATILIDADE_FAVORAVEL = {
    (PerfilRisco.CONSERVADOR, Volatilidade.BAIXA),
    (PerfilRisco.MODERADO, Volatilidade.MEDIA),
    (PerfilRisco.ARROJADO, Volatilidade.ALTA),
}

VOLATILIDADE_DESFAVORAVEL = {
    (PerfilRisco.CONSERVADOR, Volatilidade.ALTA),
}

SCORE_MINIMO = 0
SCORE_MAXIMO = 100
LIMIAR_ALTA = 70
LIMIAR_MEDIA = 40

PESOS_FIXA = {
    "indexador_previsivel_conservador": 20,
    "indexador_arrojado_prefixado": 15,
    "indexador_protege_inflacao": 20,
    "vencimento_dentro_horizonte": 20,
    "vencimento_muito_alem_horizonte": -15,
    "liquidez_diaria_curto_prazo": 15,
    "isento_ir_renda_passiva": 10,
    "investimento_acessivel": 10,
    "garantia_fgc_conservador": 10,
}

INDEXADORES_PREVISIVEIS = {Indexador.SELIC, Indexador.CDI}

DIAS_LIMITE_CURTO_PRAZO = 365
DIAS_LIMITE_MEDIO_PRAZO = 1825  # ~5 anos

HORIZONTE_ORDEM = [
    HorizonteInvestimento.CURTO_PRAZO,
    HorizonteInvestimento.MEDIO_PRAZO,
    HorizonteInvestimento.LONGO_PRAZO,
]