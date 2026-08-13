import logging

from app.models import AtivoFixoSchema, ResumoRequestSchema, ResumoResponseSchema
from app.models.enums import ModuloRanking
from app.prompts import fixa_template, variavel_template
from app.services.llm_client import LlmIndisponivelError, gerar_texto

logger = logging.getLogger(__name__)


def gerar_resumo(request: ResumoRequestSchema) -> ResumoResponseSchema:
    prompt = _montar_prompt(request)

    try:
        texto = gerar_texto(prompt)
        return ResumoResponseSchema(correlationId=request.correlationId, resumo=texto, erro=None)
    except LlmIndisponivelError as e:
        logger.warning("LLM indisponível, retornando fallback: %s", e)
        return ResumoResponseSchema(
            correlationId=request.correlationId,
            resumo=_resumo_fallback(request),
            erro="Resumo simplificado — análise via IA temporariamente indisponível.",
        )


def _montar_prompt(request: ResumoRequestSchema) -> str:
    if request.modulo == ModuloRanking.VARIAVEL:
        return variavel_template.montar_prompt(request.ativo, request.perfil)
    return fixa_template.montar_prompt(request.ativo, request.perfil)


def _resumo_fallback(request: ResumoRequestSchema) -> str:
    """
    Resumo de template simples (sem LLM). Conforme documentado: nunca deixar
    o usuário sem resposta por causa de falha externa.
    """
    ativo = request.ativo
    if isinstance(ativo, AtivoFixoSchema):
        return (
            f"{ativo.codigo} é um título {ativo.tipo.value} indexado a {ativo.indexador.value}, "
            f"com taxa de {ativo.taxaPercentual}%. Análise detalhada indisponível no momento."
        )
    return (
        f"{ativo.codigo} está sendo negociado a R$ {ativo.preco}, com DY de {ativo.dy}%. "
        f"Análise detalhada indisponível no momento."
    )