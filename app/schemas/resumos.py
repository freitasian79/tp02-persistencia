from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    StatusAtividade, StatusEvento, TipoAtividade, TipoEvento, TipoLocal,
)


class _Resumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LocalResumo(_Resumo):
    id: int
    nome: str
    tipo: TipoLocal
    capacidade: int


class EventoResumo(_Resumo):
    id: int
    nome: str
    tipo: TipoEvento
    status: StatusEvento


class PalestranteResumo(_Resumo):
    id: int
    nome: str
    area_atuacao: str | None


class ParticipanteResumo(_Resumo):
    id: int
    nome: str
    email: str


class AtividadeResumo(_Resumo):
    id: int
    evento_id: int
    titulo: str
    tipo: TipoAtividade
    inicio: datetime
    fim: datetime
    capacidade: int
    status: StatusAtividade
    local: LocalResumo