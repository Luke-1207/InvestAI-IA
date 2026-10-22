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

# Mesmos textos do Java (AcaoPontuacaoService e RendaFixaPontuacaoService), mostrados ao usuário no detalhe.
DESCRICOES_VARIAVEL = {
    "volatilidade_ideal": "Oscilação de preço compatível com o seu perfil de risco",
    "volatilidade_proxima": "Oscilação de preço aceitável para o seu perfil de risco",
    "volatilidade_alta_demais": "Oscila mais do que o seu perfil de risco costuma tolerar",
    "volatilidade_baixa_demais": "Oscila pouco para quem aceita mais risco em busca de retorno",
    "dy_renda_passiva": "Paga bons dividendos, alinhado ao seu objetivo de renda passiva",
    "dy_renda_passiva_parcial": "Paga dividendos moderados, o que ajuda no objetivo de renda passiva",
    "dy_crescimento": "Reinveste a maior parte do lucro, alinhado ao crescimento de patrimônio",
    "dy_crescimento_parcial": "Divide o lucro entre dividendos e crescimento",
    "dy_crescimento_fraco": "Distribui boa parte do lucro, o que deixa menos espaço para crescer",
    "dy_preservar": "Distribui parte do lucro, característica de empresas mais maduras",
    "dy_preservar_fraco": "Paga poucos dividendos, comum em empresas que ainda estão crescendo",
    "horizonte_longo": "Renda variável combina com o seu horizonte de longo prazo",
    "horizonte_medio": "Seu horizonte de médio prazo comporta uma parte em renda variável",
    "preco_acessivel": "O preço de uma cota cabe no valor que você tem disponível",
    "setor_preferido": "Setor está entre os que você quer ver com destaque",
    "setor_neutro": "Setor sem preferência sua, conta como neutro",
    "setor_evitado": "Setor está entre os que você prefere evitar",
}

DESCRICOES_FIXA = {
    "indexador_ideal": "Indexador mais indicado para o seu perfil de risco",
    "indexador_adequado": "Indexador que combina bem com o seu perfil de risco",
    "indexador_aceitavel": "Indexador possível para o seu perfil, mas não o mais indicado",
    "vencimento_no_horizonte": "Vence dentro do prazo em que você pretende usar o dinheiro",
    "vencimento_proximo_horizonte": "Vence um pouco antes ou depois do prazo que você informou",
    "vencimento_muito_alem_horizonte": "Vence muito longe do prazo em que você pretende usar o dinheiro",
    "liquidez_diaria": "Liquidez diária: você pode resgatar quando precisar",
    "liquidez_no_vencimento_longo": "Resgate só no vencimento, sem problema para o seu horizonte de longo prazo",
    "liquidez_no_vencimento_medio": "Resgate só no vencimento, aceitável para o seu horizonte de médio prazo",
    "isento_ir_renda_passiva": "Isento de Imposto de Renda, o que aumenta a renda que chega até você",
    "renda_passiva_tributada": "Paga Imposto de Renda, o que reduz um pouco a renda líquida",
    "indexador_protege_inflacao": "Atrelado ao IPCA, protege o seu dinheiro da inflação",
    "pos_fixado_preservar": "Rende acompanhando os juros, de forma estável",
    "prefixado_preservar": "Taxa fixa pode perder para a inflação, menos indicada para preservar capital",
    "taxa_crescimento": "Taxa travada ou ligada à inflação, boa para crescer no longo prazo",
    "pos_fixado_crescimento": "Rende acompanhando os juros, com crescimento mais modesto no longo prazo",
    "investimento_acessivel": "O investimento mínimo cabe no valor que você tem disponível",
    "garantia_tesouro": "Título público, garantido pelo Tesouro Nacional",
    "garantia_fgc": "Garantido pelo FGC até R$ 250 mil por CPF em cada instituição",
}

HORIZONTE_ORDEM = [
    HorizonteInvestimento.CURTO_PRAZO,
    HorizonteInvestimento.MEDIO_PRAZO,
    HorizonteInvestimento.LONGO_PRAZO,
]
