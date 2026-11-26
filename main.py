from pydantic import BaseModel, ConfigDict
from app.schemas.presenca import PresencaCreate, PresencaRead
from app.schemas.resumos import AtividadeResumo, ParticipanteResumo

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import Base, engine, get_db
from app.core.exceptions import registrar_handlers
from app.models.enums import StatusAtividade, StatusInscricao
from app.routers import atividades, eventos, locais, palestrantes, participantes
from app.schemas.common import Page
from app.schemas.inscricao import InscricaoRead
from app.services.common import paginar

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Gestão de Eventos - TP02")
registrar_handlers(app)

app.include_router(locais.router)
app.include_router(eventos.router)
app.include_router(participantes.router)
app.include_router(palestrantes.router)
app.include_router(atividades.router)

@app.post("/inscricoes/", response_model=schemas.InscricaoRead, status_code=status.HTTP_201_CREATED)
def criar_inscricao(inscricao: schemas.InscricaoCreate, db: Session = Depends(get_db)):
    db_participante = db.query(models.Participante).filter(models.Participante.id == inscricao.participante_id).first()
    if not db_participante or not db_participante.ativo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Participante inativo ou inexistente")

    db_atividade = db.query(models.Atividade).filter(models.Atividade.id == inscricao.atividade_id).first()
    if not db_atividade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atividade não encontrada")

    inscricao_existente = db.query(models.Inscricao).filter(
        models.Inscricao.participante_id == inscricao.participante_id,
        models.Inscricao.atividade_id == inscricao.atividade_id,
        models.Inscricao.status == "confirmada"
    ).first()

    if inscricao_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Participante já inscrito nesta atividade")

    total_inscritos = db.query(models.Inscricao).filter(
        models.Inscricao.atividade_id == inscricao.atividade_id,
        models.Inscricao.status == "confirmada"
    ).count()

    capacidade_maxima = db_atividade.local.capacidade if db_atividade.local else 0
    if total_inscritos >= capacidade_maxima:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Atividade sem vagas disponíveis")

    db_inscricao = models.Inscricao(**inscricao.model_dump())
    db.add(db_inscricao)
    db.commit()
    db.refresh(db_inscricao)
    return db_inscricao

@app.get("/inscricoes/", response_model=Page[InscricaoRead])
def listar_inscricoes(
    status: StatusInscricao | None = None,
    participante_id: int | None = None,
    atividade_id: int | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.Inscricao)
    if status:
        query = query.filter(models.Inscricao.status == status)
    if participante_id:
        query = query.filter(models.Inscricao.participante_id == participante_id)
    if atividade_id:
        query = query.filter(models.Inscricao.atividade_id == atividade_id)
    return paginar(query, offset, limit)

@app.patch("/inscricoes/{inscricao_id}/status", response_model=schemas.InscricaoRead)
def mudar_status_inscricao(inscricao_id: int, novo_status: StatusInscricao, db: Session = Depends(get_db)):
    db_inscricao = db.query(models.Inscricao).filter(models.Inscricao.id == inscricao_id).first()
    if not db_inscricao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada")

    db_inscricao.status = novo_status
    db.commit()
    db.refresh(db_inscricao)
    return db_inscricao

class ItemProgramacao(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inscricao_id: int
    status_inscricao: StatusInscricao
    presente: bool
    atividade: AtividadeResumo


class ProgramacaoParticipante(BaseModel):
    participante: ParticipanteResumo
    atividades: list[ItemProgramacao]


@app.post("/presencas/", response_model=PresencaRead, status_code=status.HTTP_201_CREATED)
def registrar_presenca(presenca: PresencaCreate, db: Session = Depends(get_db)):
    db_inscricao = db.query(models.Inscricao).filter(models.Inscricao.id == presenca.inscricao_id).first()
    if not db_inscricao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada")

    if not db_inscricao.participante.ativo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Participante inativo")

    if db_inscricao.status != StatusInscricao.CONFIRMADA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas inscrições confirmadas podem registrar presença",
        )

    if db_inscricao.atividade.status == StatusAtividade.CANCELADA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível registrar presença em atividade cancelada",
        )

    if db_inscricao.presenca is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Presença já registrada para esta inscrição",
        )

    db_presenca = models.Presenca(**presenca.model_dump())
    db.add(db_presenca)
    db.commit()
    db.refresh(db_presenca)
    return db_presenca


@app.get("/presencas/", response_model=Page[PresencaRead])
def listar_presencas(
    inscricao_id: int | None = None,
    atividade_id: int | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.Presenca)
    if inscricao_id is not None:
        query = query.filter(models.Presenca.inscricao_id == inscricao_id)
    if atividade_id is not None:
        query = query.join(models.Inscricao).filter(models.Inscricao.atividade_id == atividade_id)
    return paginar(query, offset, limit)


@app.get("/inscricoes/{inscricao_id}/presenca", response_model=PresencaRead)
def obter_presenca_inscricao(inscricao_id: int, db: Session = Depends(get_db)):
    db_inscricao = db.query(models.Inscricao).filter(models.Inscricao.id == inscricao_id).first()
    if not db_inscricao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada")
    if not db_inscricao.presenca:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presença ainda não registrada")
    return db_inscricao.presenca


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