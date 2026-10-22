import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT_SEGUNDOS = 15.0
MAX_TOKENS_RESPOSTA = 300
MAX_TOKENS_COM_RACIOCINIO = 1500
PREFIXOS_MODELOS_COM_RACIOCINIO = ("openai/gpt-oss",)


class LlmIndisponivelError(Exception):
    """Lançada quando a chamada ao LLM falha, expira o timeout, ou o provider configurado não é suportado."""


def _montar_payload(prompt: str) -> dict:
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": MAX_TOKENS_RESPOSTA,
    }
    if settings.LLM_MODEL.startswith(PREFIXOS_MODELOS_COM_RACIOCINIO):
        payload["max_tokens"] = MAX_TOKENS_COM_RACIOCINIO
        payload["reasoning_effort"] = "low"
        payload["include_reasoning"] = False
    return payload


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
            json=_montar_payload(prompt),
            timeout=TIMEOUT_SEGUNDOS,
        )
        response.raise_for_status()
        dados = response.json()
        texto = (dados["choices"][0]["message"]["content"] or "").strip()

    except httpx.HTTPStatusError as e:
        logger.error(
            "LLM (%s, modelo %s) respondeu HTTP %s: %s",
            settings.LLM_PROVIDER, settings.LLM_MODEL, e.response.status_code, e.response.text,
        )
        raise LlmIndisponivelError(str(e)) from e
    except (httpx.HTTPError, KeyError, IndexError, TypeError) as e:
        logger.error("Falha ao chamar o LLM (%s): %s", settings.LLM_PROVIDER, e)
        raise LlmIndisponivelError(str(e)) from e

    if not texto:
        logger.error("LLM (%s, modelo %s) devolveu resposta vazia", settings.LLM_PROVIDER, settings.LLM_MODEL)
        raise LlmIndisponivelError("Resposta vazia do LLM")
    return texto