from pydantic import BaseModel, EmailStr
from typing import Optional

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