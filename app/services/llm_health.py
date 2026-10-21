import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
TIMEOUT_SEGUNDOS = 5.0
VALIDADE_CACHE_SEGUNDOS = 60.0

_ultimo_resultado: dict | None = None
_verificado_em: float = 0.0


def _resultado(disponivel: bool, detalhe: str | None = None) -> dict:
    return {
        "disponivel": disponivel,
        "provider": settings.LLM_PROVIDER,
        "modelo": settings.LLM_MODEL,
        "detalhe": detalhe,
    }


def _consultar_provider() -> dict:
    if settings.LLM_PROVIDER != "groq":
        return _resultado(False, f"Provider '{settings.LLM_PROVIDER}' não suportado")
    if not settings.LLM_API_KEY:
        return _resultado(False, "Chave de API do LLM não configurada")

    try:
        response = httpx.get(
            f"{GROQ_MODELS_URL}/{settings.LLM_MODEL}",
            headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
            timeout=TIMEOUT_SEGUNDOS,
        )
    except httpx.HTTPError as e:
        logger.warning("Health do LLM: sem resposta do provider (%s)", e)
        return _resultado(False, "O provedor do LLM não respondeu")

    if response.status_code == 200:
        return _resultado(True)
    if response.status_code in (401, 403):
        return _resultado(False, "O provedor recusou a chave de API")
    if response.status_code == 404:
        return _resultado(False, f"Modelo '{settings.LLM_MODEL}' não encontrado no provedor")
    if response.status_code == 429:
        return _resultado(False, "Limite de uso do provedor atingido")
    return _resultado(False, f"O provedor respondeu HTTP {response.status_code}")


def verificar_llm(forcar: bool = False) -> dict:
    """Usa o endpoint de modelos da Groq, que não consome tokens, e guarda o resultado por um minuto."""
    global _ultimo_resultado, _verificado_em
    agora = time.monotonic()
    if not forcar and _ultimo_resultado is not None and agora - _verificado_em < VALIDADE_CACHE_SEGUNDOS:
        return _ultimo_resultado

    _ultimo_resultado = _consultar_provider()
    _verificado_em = agora
    return _ultimo_resultado


def limpar_cache() -> None:
    global _ultimo_resultado, _verificado_em
    _ultimo_resultado = None
    _verificado_em = 0.0
