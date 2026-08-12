from app.models import AtivoRankeadoSchema, RankingRequestSchema, RankingResponseSchema


def ranquear(request: RankingRequestSchema) -> RankingResponseSchema:
    """
    STUB TEMPORÁRIO. O algoritmo real de pontuação (critérios e pesos por
    perfil, conforme documentado) é implementado no INVAI-44. Esta função
    hoje só valida o contrato de entrada/saída ponta a ponta via HTTP —
    todo ativo recebe o mesmo score fixo, sem nenhuma lógica de negócio.
    """
    ativos_rankeados = [
        AtivoRankeadoSchema(
            codigo=ativo.codigo,
            score=50,
            compatibilidade="MEDIA",
            justificativa="Stub temporário — algoritmo real chega no INVAI-44.",
        )
        for ativo in request.ativos
    ]
    return RankingResponseSchema(correlationId=request.correlationId, ativos=ativos_rankeados)