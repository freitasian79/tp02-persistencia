from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import StatusEvento, TipoEvento


class EventoBase(BaseModel):
    nome: str = Field(min_length=3, max_length=150, examples=["Semana de Tecnologia 2026"])
    descricao: str | None = None
    tipo: TipoEvento
    data_inicio: date
    data_fim: date
    organizador: str | None = Field(default=None, max_length=150)

    @model_validator(mode="after")
    def validar_periodo(self):
        if self.data_fim < self.data_inicio:
            raise ValueError("data_fim deve ser igual ou posterior a data_inicio")
        return self


class EventoCreate(EventoBase):
    pass


class EventoUpdate(BaseModel):
    """Status não é alterado aqui: use POST /eventos/{id}/cancelar."""

    nome: str | None = Field(default=None, min_length=3, max_length=150)
    descricao: str | None = None
    tipo: TipoEvento | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    organizador: str | None = Field(default=None, max_length=150)


class EventoRead(EventoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: StatusEvento
    criado_em: datetime


class EventoCancelamento(BaseModel):
    evento_id: int
    status: StatusEvento
    atividades_canceladas: int
    inscricoes_canceladas: int