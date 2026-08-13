from typing import List, Union
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.ativo import AtivoFixoSchema, AtivoVariavelSchema
from app.models.enums import Compatibilidade, ModuloRanking
from app.models.perfil import PerfilSchema
from typing import List, Optional, Union


class RankingRequestSchema(BaseModel):
    correlationId: UUID
    modulo: ModuloRanking
    perfil: PerfilSchema
    ativos: List[Union[AtivoVariavelSchema, AtivoFixoSchema]] = Field(default_factory=list)
    erro: Optional[str] = None

    @model_validator(mode="after")
    def ativos_devem_condizer_com_modulo(self) -> "RankingRequestSchema":
        tipo_esperado = AtivoVariavelSchema if self.modulo == ModuloRanking.VARIAVEL else AtivoFixoSchema
        for ativo in self.ativos:
            if not isinstance(ativo, tipo_esperado):
                raise ValueError(
                    f"modulo={self.modulo.value} espera ativos do tipo "
                    f"{tipo_esperado.__name__}, mas recebeu {type(ativo).__name__}"
                )
        return self


class AtivoRankeadoSchema(BaseModel):
    codigo: str = Field(..., min_length=1)
    score: int = Field(..., ge=0, le=100, description="Score de compatibilidade, 0-100")
    compatibilidade: Compatibilidade
    justificativa: str


class RankingResponseSchema(BaseModel):
    correlationId: UUID
    ativos: List[AtivoRankeadoSchema] = Field(default_factory=list)