from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel

from app.models.ativo import AtivoFixoSchema, AtivoVariavelSchema
from app.models.enums import ModuloRanking
from app.models.perfil import PerfilSchema


class ResumoRequestSchema(BaseModel):
    correlationId: UUID
    modulo: ModuloRanking
    perfil: PerfilSchema
    ativo: Union[AtivoVariavelSchema, AtivoFixoSchema]


class ResumoResponseSchema(BaseModel):
    correlationId: UUID
    resumo: Optional[str] = None
    erro: Optional[str] = None