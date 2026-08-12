from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import Indexador, Liquidez, TipoAtivoFixo, TipoAtivoVariavel, Volatilidade


class Variacao52SemanasSchema(BaseModel):
    min: float = Field(..., ge=0)
    max: float = Field(..., ge=0)


class AtivoVariavelSchema(BaseModel):
    """
    Representa uma ação, FII ou ETF nos dois contextos em que o microsserviço
    a recebe: ranqueamento (campos essenciais) e resumo em linguagem natural
    (campos adicionais). Os campos exclusivos de cada contexto são opcionais.
    """
    codigo: str = Field(..., min_length=1)
    nome: Optional[str] = None
    tipo: TipoAtivoVariavel
    setor: str
    preco: float = Field(..., gt=0)
    dy: float = Field(..., ge=0, description="Dividend Yield em %")
    variacao30d: float

    # Exclusivo do ranqueamento
    volatilidade: Optional[Volatilidade] = None

    # Exclusivos do resumo em linguagem natural
    pl: Optional[float] = Field(default=None, gt=0)
    pvp: Optional[float] = Field(default=None, gt=0)
    variacao52s: Optional[Variacao52SemanasSchema] = None
    mediaSetorialDY: Optional[float] = Field(default=None, ge=0)


class AtivoFixoSchema(BaseModel):
    """
    Representa um título de renda fixa (Tesouro, CDB, LCI ou LCA) nos dois
    contextos em que o microsserviço o recebe: ranqueamento e resumo.
    """
    codigo: str = Field(..., min_length=1)
    nome: Optional[str] = None
    emissor: Optional[str] = None
    tipo: TipoAtivoFixo
    indexador: Indexador
    taxaPercentual: float = Field(..., gt=0)
    vencimento: date
    investimentoMinimo: float = Field(..., ge=0)
    liquidez: Liquidez
    isentoIR: bool = False
    garantidoFGC: bool = False

    # Exclusivo do resumo em linguagem natural (referência de mercado)
    selicAtual: Optional[float] = Field(default=None, ge=0)