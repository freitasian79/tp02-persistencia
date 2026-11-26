from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import StatusAtividade, TipoAtividade
from app.schemas.common import para_naive
from app.schemas.resumos import EventoResumo, LocalResumo, PalestranteResumo


class AtividadeCreate(BaseModel):
    evento_id: int = Field(gt=0)
    local_id: int = Field(gt=0)
    titulo: str = Field(min_length=3, max_length=200)
    descricao: str | None = None
    tipo: TipoAtividade
    inicio: datetime
    fim: datetime
    capacidade: int = Field(gt=0, le=10000)
    palestrante_ids: list[int] = Field(default_factory=list)

    _naive = field_validator("inicio", "fim")(para_naive)

    @model_validator(mode="after")
    def validar_horario(self):
        if self.fim <= self.inicio:
            raise ValueError("fim deve ser posterior a inicio")
        if len(set(self.palestrante_ids)) != len(self.palestrante_ids):
            raise ValueError("palestrante_ids contém valores repetidos")
        return self


class AtividadeUpdate(BaseModel):
    local_id: int | None = Field(default=None, gt=0)
    titulo: str | None = Field(default=None, min_length=3, max_length=200)
    descricao: str | None = None
    tipo: TipoAtividade | None = None
    inicio: datetime | None = None
    fim: datetime | None = None
    capacidade: int | None = Field(default=None, gt=0, le=10000)
    palestrante_ids: list[int] | None = None
    motivo_alteracao: str | None = Field(default=None, max_length=255)

    _naive = field_validator("inicio", "fim")(para_naive)


class AtividadeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descricao: str | None
    tipo: TipoAtividade
    inicio: datetime
    fim: datetime
    capacidade: int
    status: StatusAtividade
    evento: EventoResumo
    local: LocalResumo
    palestrantes: list[PalestranteResumo]
    vagas_disponiveis: int | None = None