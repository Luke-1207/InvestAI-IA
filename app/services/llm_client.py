import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT_SEGUNDOS = 15.0


class LlmIndisponivelError(Exception):
    """Lançada quando a chamada ao LLM falha, expira o timeout, ou o provider configurado não é suportado."""


def gerar_texto(prompt: str) -> str:
    if settings.LLM_PROVIDER != "groq":
        raise LlmIndisponivelError(
            f"Provider '{settings.LLM_PROVIDER}' não suportado nesta implementação (só 'groq' por enquanto)."
        )

    try:
        response = httpx.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 300,
            },
            timeout=TIMEOUT_SEGUNDOS,
        )
        response.raise_for_status()
        dados = response.json()
        return dados["choices"][0]["message"]["content"].strip()

    except (httpx.HTTPError, KeyError, IndexError) as e:
        logger.error("Falha ao chamar o LLM (%s): %s", settings.LLM_PROVIDER, e)
        raise LlmIndisponivelError(str(e)) from e