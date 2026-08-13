from app.models.enums import PerfilRisco, Volatilidade

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