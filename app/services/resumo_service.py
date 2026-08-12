from app.models import ResumoRequestSchema, ResumoResponseSchema


def gerar_resumo(request: ResumoRequestSchema) -> ResumoResponseSchema:
    """
    STUB TEMPORÁRIO. A integração real com o LLM externo (prompt + chamada
    httpx) fica para a sprint dedicada ao microsserviço de resumos.
    """
    return ResumoResponseSchema(
        correlationId=request.correlationId,
        resumo="Resumo de exemplo (stub) — integração real com o LLM ainda não implementada.",
        erro=None,
    )