from fastapi import FastAPI

from app.api import health
from app.config import settings


def create_app(enable_preview: bool | None = None) -> FastAPI:
    app = FastAPI(
        title="InvestAI - Microsserviço IA",
        description="Ranqueamento de ativos por perfil e geração de resumos em linguagem natural.",
        version="0.4.0",
    )

    app.include_router(health.router)

    preview_habilitado = settings.ENABLE_PREVIEW_ENDPOINTS if enable_preview is None else enable_preview
    if preview_habilitado:
        from app.api import preview
        app.include_router(preview.router)

    return app


app = create_app()