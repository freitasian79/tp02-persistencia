from pydantic import BaseModel, ConfigDict
from app.schemas.resumos import AtividadeResumo, ParticipanteResumo

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.core.database import Base, engine, get_db
from app.core.exceptions import registrar_handlers
from app.models.enums import StatusInscricao
from app.routers import (
    atividades,
    eventos,
    inscricoes,
    locais,
    palestrantes,
    participantes,
    presencas,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Gestão de Eventos - TP02")
registrar_handlers(app)

app.include_router(locais.router)
app.include_router(eventos.router)
app.include_router(participantes.router)
app.include_router(palestrantes.router)
app.include_router(atividades.router)
app.include_router(inscricoes.router)
app.include_router(presencas.router)


class ItemProgramacao(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inscricao_id: int
    status_inscricao: StatusInscricao
    presente: bool
    atividade: AtividadeResumo


class ProgramacaoParticipante(BaseModel):
    participante: ParticipanteResumo
    atividades: list[ItemProgramacao]


@app.get("/participantes/{participante_id}/programacao", response_model=ProgramacaoParticipante)
def obter_programacao_participante(
    participante_id: int,
    evento_id: int | None = None,
    db: Session = Depends(get_db),
):
    db_participante = db.query(models.Participante).filter(models.Participante.id == participante_id).first()
    if not db_participante:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participante não encontrado")

    query = (
        db.query(models.Inscricao)
        .join(models.Atividade)
        .filter(
            models.Inscricao.participante_id == participante_id,
            models.Inscricao.status != StatusInscricao.CANCELADA,
        )
        .order_by(models.Atividade.inicio.asc())
    )

    if evento_id is not None:
        query = query.filter(models.Atividade.evento_id == evento_id)

    inscricoes = query.all()
    itens = [
        ItemProgramacao(
            inscricao_id=insc.id,
            status_inscricao=insc.status,
            presente=insc.presenca is not None,
            atividade=insc.atividade,
        )
        for insc in inscricoes
    ]

    return ProgramacaoParticipante(
        participante=db_participante,
        atividades=itens,
    )