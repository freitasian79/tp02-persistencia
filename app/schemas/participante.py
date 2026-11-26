import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _normalizar_cpf(valor: str | None) -> str | None:
    if valor is None:
        return None
    digitos = re.sub(r"\D", "", valor)
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        raise ValueError("CPF deve conter 11 dígitos válidos")
    return digitos


class ParticipanteBase(BaseModel):
    nome: str = Field(min_length=3, max_length=150)
    email: EmailStr
    telefone: str | None = Field(default=None, max_length=20)
    instituicao: str | None = Field(default=None, max_length=150)


class ParticipanteCreate(ParticipanteBase):
    cpf: str = Field(examples=["123.456.789-09"])

    _cpf = field_validator("cpf")(_normalizar_cpf)


class ParticipanteUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=3, max_length=150)
    email: EmailStr | None = None
    telefone: str | None = Field(default=None, max_length=20)
    instituicao: str | None = Field(default=None, max_length=150)
    ativo: bool | None = None


class ParticipanteRead(ParticipanteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cpf: str
    ativo: bool
    criado_em: datetime