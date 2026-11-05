from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class ParticipanteBase(BaseModel):
    nome: str
    email: EmailStr

class ParticipanteCreate(ParticipanteBase):
    pass

class ParticipanteUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    ativo: Optional[bool] = None

class ParticipanteResponse(ParticipanteBase):
    id: int
    ativo: bool

    class Config:
        from_attributes = True

class PalestranteBase(BaseModel):
    nome: str
    email: EmailStr
    especialidade: Optional[str] = None

class PalestranteCreate(PalestranteBase):
    pass

class PalestranteUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    especialidade: Optional[str] = None

class PalestranteResponse(PalestranteBase):
    id: int

    class Config:
        from_attributes = True

class AtividadeBase(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    inicio: datetime
    fim: datetime
    vagas: int
    ativa: bool = True
    evento_id: int
    local_id: int

class AtividadeCreate(AtividadeBase):
    palestrantes_ids: List[int] = []

class AtividadeUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    inicio: Optional[datetime] = None
    fim: Optional[datetime] = None
    vagas: Optional[int] = None
    ativa: Optional[bool] = None
    evento_id: Optional[int] = None
    local_id: Optional[int] = None
    palestrantes_ids: Optional[List[int]] = None

class AtividadeResponse(AtividadeBase):
    id: int
    palestrantes: List[PalestranteResponse] = []

    class Config:
        from_attributes = True