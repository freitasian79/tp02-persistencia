from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatusInscricao
from app.schemas.resumos import AtividadeResumo, ParticipanteResumo


class InscricaoCreate(BaseModel):
    participante_id: int = Field(gt=0)
    atividade_id: int = Field(gt=0)
    observacao: str | None = Field(default=None, max_length=255)


class InscricaoStatusUpdate(BaseModel):
    status: StatusInscricao
    observacao: str | None = Field(default=None, max_length=255)


class InscricaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    participante_id: int
    atividade_id: int
    status: StatusInscricao
    data_inscricao: datetime
    atualizada_em: datetime | None
    observacao: str | None


class InscricaoDetalhe(InscricaoRead):
    participante: ParticipanteResumo
    atividade: AtividadeResumo