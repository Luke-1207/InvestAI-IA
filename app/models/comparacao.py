from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel

from app.models.ativo import AtivoFixoSchema, AtivoVariavelSchema
from app.models.perfil import PerfilSchema


class ComparacaoRequestSchema(BaseModel):
    correlationId: UUID
    perfil: PerfilSchema
    ativoA: Union[AtivoVariavelSchema, AtivoFixoSchema]
    ativoB: Union[AtivoVariavelSchema, AtivoFixoSchema]


class ComparacaoResponseSchema(BaseModel):
    correlationId: UUID
    veredito: Optional[str] = None
    erro: Optional[str] = None