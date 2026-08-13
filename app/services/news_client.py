import logging
from typing import List

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

NEWS_API_URL = "https://newsapi.org/v2/everything"
TIMEOUT_SEGUNDOS = 8.0
MAX_NOTICIAS = 3


def buscar_manchetes_recentes(termo_busca: str) -> List[str]:
    """
    Enriquecimento opcional do resumo — nunca pode bloquear a geração do
    texto. Sem NEWS_API_KEY configurada, retorna lista vazia imediatamente
    (sem chamada de rede). Qualquer falha também degrada para lista vazia.
    """
    if not settings.NEWS_API_KEY:
        logger.debug("NEWS_API_KEY não configurada — pulando busca de notícias.")
        return []

    try:
        response = httpx.get(
            NEWS_API_URL,
            params={
                "q": termo_busca, "language": "pt", "sortBy": "publishedAt",
                "pageSize": MAX_NOTICIAS, "apiKey": settings.NEWS_API_KEY,
            },
            timeout=TIMEOUT_SEGUNDOS,
        )
        response.raise_for_status()
        artigos = response.json().get("articles", [])
        return [artigo["title"] for artigo in artigos if artigo.get("title")]

    except (httpx.HTTPError, KeyError) as e:
        logger.warning("Falha ao buscar notícias para '%s': %s", termo_busca, e)
        return []