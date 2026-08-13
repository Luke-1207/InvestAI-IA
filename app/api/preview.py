from fastapi import APIRouter

from app.models import (
    RankingRequestSchema,
    RankingResponseSchema,
    ResumoRequestSchema,
    ResumoResponseSchema,
)
from app.services import ranking_service, resumo_service

router = APIRouter(tags=["Preview (desenvolvimento)"])


@router.post(
    "/ranking/preview",
    response_model=RankingResponseSchema,
    summary="Testa o ranqueamento diretamente via HTTP, sem passar pelo RabbitMQ",
)
def preview_ranking(request: RankingRequestSchema) -> RankingResponseSchema:
    return ranking_service.ranquear(request)


@router.post(
    "/resumo/preview",
    response_model=ResumoResponseSchema,
    summary="Testa a geração de resumo em linguagem natural diretamente via HTTP, sem passar pelo RabbitMQ",
)
def preview_resumo(request: ResumoRequestSchema) -> ResumoResponseSchema:
    return resumo_service.gerar_resumo(request)