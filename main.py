import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def _iniciar_consumers_em_threads() -> None:
    from app.consumers import ranking_consumer, resumo_consumer

    threading.Thread(target=ranking_consumer.iniciar, name="ranking-consumer", daemon=True).start()
    threading.Thread(target=resumo_consumer.iniciar, name="resumo-consumer", daemon=True).start()


def create_app(enable_preview: bool | None = None, start_consumers: bool = True) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if start_consumers:
            _iniciar_consumers_em_threads()
        yield
        # Threads são daemon=True — encerram junto com o processo principal

    app = FastAPI(
        title="InvestAI - Microsserviço IA",
        description="Ranqueamento de ativos por perfil e geração de resumos em linguagem natural.",
        version="0.6.0",
        lifespan=lifespan,
    )

    app.include_router(health.router)

    preview_habilitado = settings.ENABLE_PREVIEW_ENDPOINTS if enable_preview is None else enable_preview
    if preview_habilitado:
        from app.api import preview
        app.include_router(preview.router)

    return app


app = create_app()