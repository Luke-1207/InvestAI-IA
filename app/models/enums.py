from enum import Enum


class PerfilRisco(str, Enum):
    CONSERVADOR = "CONSERVADOR"
    MODERADO = "MODERADO"
    ARROJADO = "ARROJADO"


class HorizonteInvestimento(str, Enum):
    CURTO_PRAZO = "CURTO_PRAZO"
    MEDIO_PRAZO = "MEDIO_PRAZO"
    LONGO_PRAZO = "LONGO_PRAZO"


class ObjetivoFinanceiro(str, Enum):
    RENDA_PASSIVA = "RENDA_PASSIVA"
    CRESCIMENTO_PATRIMONIO = "CRESCIMENTO_PATRIMONIO"
    PRESERVAR_CAPITAL = "PRESERVAR_CAPITAL"


class PreferenciaSetor(str, Enum):
    PREFERIR = "PREFERIR"
    EVITAR = "EVITAR"


class TipoAtivoVariavel(str, Enum):
    ACAO = "ACAO"
    FII = "FII"
    ETF = "ETF"


class TipoAtivoFixo(str, Enum):
    TESOURO = "TESOURO"
    CDB = "CDB"
    LCI = "LCI"
    LCA = "LCA"


class Indexador(str, Enum):
    SELIC = "SELIC"
    CDI = "CDI"
    IPCA = "IPCA"
    PREFIXADO = "PREFIXADO"


class Liquidez(str, Enum):
    DIARIA = "DIARIA"
    NO_VENCIMENTO = "NO_VENCIMENTO"


class Volatilidade(str, Enum):
    BAIXA = "BAIXA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"


class ModuloRanking(str, Enum):
    VARIAVEL = "VARIAVEL"
    FIXA = "FIXA"


class Compatibilidade(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAIXA = "BAIXA"