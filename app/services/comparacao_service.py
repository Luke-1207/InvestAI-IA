import logging

from app.models import ComparacaoRequestSchema, ComparacaoResponseSchema
from app.prompts import comparacao_template
from app.services.llm_client import LlmIndisponivelError, gerar_texto

logger = logging.getLogger(__name__)


def gerar_veredito(request: ComparacaoRequestSchema) -> ComparacaoResponseSchema:
    prompt = comparacao_template.montar_prompt(request.ativoA, request.ativoB, request.perfil)

    try:
        texto = gerar_texto(prompt)
        return ComparacaoResponseSchema(correlationId=request.correlationId, veredito=texto, erro=None)
    except LlmIndisponivelError as e:
        logger.warning("LLM indisponível, retornando fallback: %s", e)
        return ComparacaoResponseSchema(
            correlationId=request.correlationId,
            veredito=_veredito_fallback(request),
            erro="Veredito simplificado — análise via IA temporariamente indisponível.",
        )


def _veredito_fallback(request: ComparacaoRequestSchema) -> str:
    return (
        f"Não foi possível gerar uma análise comparativa detalhada agora. "
        f"Avalie {comparacao_template.rotulo_ativo(request.ativoA)} e "
        f"{comparacao_template.rotulo_ativo(request.ativoB)} considerando "
        f"seu perfil de risco e horizonte de investimento antes de decidir."
    )