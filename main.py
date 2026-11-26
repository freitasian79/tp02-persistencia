from pydantic import BaseModel, ConfigDict
from app.schemas.presenca import PresencaCreate, PresencaRead
from app.schemas.resumos import AtividadeResumo, ParticipanteResumo

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import Base, engine, get_db
from app.core.exceptions import registrar_handlers
from app.models.enums import (
    StatusAtividade,
    StatusInscricao,
    TipoAtividade,
)
from app.routers import eventos, locais, palestrantes, participantes
from app.schemas.atividade import AtividadeRead
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

@app.post("/atividades/", response_model=schemas.AtividadeRead, status_code=status.HTTP_201_CREATED)
def criar_atividade(atividade: schemas.AtividadeCreate, db: Session = Depends(get_db)):
    db_local = db.query(models.Local).filter(models.Local.id == atividade.local_id).first()
    if not db_local or not db_local.ativo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Local inativo ou inexistente")

    db_evento = db.query(models.Evento).filter(models.Evento.id == atividade.evento_id).first()
    if not db_evento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado")

    if atividade.inicio.date() < db_evento.data_inicio or atividade.fim.date() > db_evento.data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A atividade deve ocorrer dentro do periodo do evento"
        )

    palestrantes_db = db.query(models.Palestrante).filter(models.Palestrante.id.in_(atividade.palestrante_ids)).all()

    atividade_data = atividade.model_dump(exclude={"palestrante_ids"})
    db_atividade = models.Atividade(**atividade_data)
    db_atividade.palestrantes = palestrantes_db

    db.add(db_atividade)
    db.commit()
    db.refresh(db_atividade)
    return db_atividade

@app.get("/atividades/", response_model=Page[AtividadeRead])
def listar_atividades(
    status: StatusAtividade | None = None,
    tipo: TipoAtividade | None = None,
    evento_id: int | None = None,
    local_id: int | None = None,
    com_vagas: bool | None = None,
    nome: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.Atividade)
    if status:
        query = query.filter(models.Atividade.status == status)
    if tipo:
        query = query.filter(models.Atividade.tipo == tipo)
    if evento_id:
        query = query.filter(models.Atividade.evento_id == evento_id)
    if local_id:
        query = query.filter(models.Atividade.local_id == local_id)
    if nome:
        query = query.filter(models.Atividade.titulo.ilike(f"%{nome}%"))

    if com_vagas is not None:
        ocupadas = (
            db.query(func.count(models.Inscricao.id))
            .filter(
                models.Inscricao.atividade_id == models.Atividade.id,
                models.Inscricao.status != StatusInscricao.CANCELADA,
            )
            .correlate(models.Atividade)
            .scalar_subquery()
        )
        if com_vagas:
            query = query.filter(models.Atividade.capacidade > ocupadas)
        else:
            query = query.filter(models.Atividade.capacidade <= ocupadas)

    pagina = paginar(query, offset, limit)
    for atividade in pagina["items"]:
        qtd = sum(1 for i in atividade.inscricoes if i.status != StatusInscricao.CANCELADA)
        atividade.vagas_disponiveis = max(0, atividade.capacidade - qtd)
    return pagina

@app.get("/atividades/{atividade_id}", response_model=schemas.AtividadeRead)
def obter_atividade(atividade_id: int, db: Session = Depends(get_db)):
    db_atividade = db.query(models.Atividade).filter(models.Atividade.id == atividade_id).first()
    if not db_atividade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atividade não encontrada")
    return db_atividade

@app.put("/atividades/{atividade_id}", response_model=schemas.AtividadeRead)
def atualizar_atividade(atividade_id: int, atividade: schemas.AtividadeUpdate, db: Session = Depends(get_db)):
    db_atividade = db.query(models.Atividade).filter(models.Atividade.id == atividade_id).first()
    if not db_atividade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atividade não encontrada")

    atividade_data = atividade.model_dump(exclude_unset=True)

    if "palestrante_ids" in atividade_data:
        palestrante_ids = atividade_data.pop("palestrante_ids")
        palestrantes_db = db.query(models.Palestrante).filter(models.Palestrante.id.in_(palestrante_ids)).all()
        db_atividade.palestrantes = palestrantes_db

    for key, value in atividade_data.items():
        setattr(db_atividade, key, value)

    db.commit()
    db.refresh(db_atividade)
    return db_atividade

@app.delete("/atividades/{atividade_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_atividade(atividade_id: int, db: Session = Depends(get_db)):
    db_atividade = db.query(models.Atividade).filter(models.Atividade.id == atividade_id).first()
    if not db_atividade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atividade não encontrada")
    db.delete(db_atividade)
    db.commit()
    return None

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