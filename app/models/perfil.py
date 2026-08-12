from typing import List

from pydantic import BaseModel, Field

from app.models.enums import (
    HorizonteInvestimento,
    ObjetivoFinanceiro,
    PerfilRisco,
    PreferenciaSetor,
    TipoAtivoVariavel,
)


class SetorPreferidoSchema(BaseModel):
    setor: str = Field(..., min_length=1, description="Nome do setor econômico")
    preferencia: PreferenciaSetor


class PerfilSchema(BaseModel):
    perfilRisco: PerfilRisco
    horizonte: HorizonteInvestimento
    objetivo: ObjetivoFinanceiro
    valorDisponivel: float = Field(..., gt=0, description="Capital disponível em R$")
    tiposAceitos: List[TipoAtivoVariavel] = Field(default_factory=list)
    setoresPreferidos: List[SetorPreferidoSchema] = Field(default_factory=list)