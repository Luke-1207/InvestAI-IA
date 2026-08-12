from fastapi import FastAPI

from app.config import settings

app = FastAPI(
    title="InvestAI - Microsserviço IA",
    description="Ranqueamento de ativos por perfil e geração de resumos em linguagem natural.",
    version="0.2.0",
)

# from app.api import health
# app.include_router(health.router)