from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import Base, engine, get_db
from app.core.exceptions import registrar_handlers
from app.models.enums import (
    StatusAtividade,
    StatusEvento,
    StatusInscricao,
    TipoAtividade,
    TipoEvento,
    TipoLocal,
)
from app.schemas.atividade import AtividadeRead
from app.schemas.common import Page
from app.schemas.evento import EventoRead
from app.schemas.inscricao import InscricaoRead
from app.schemas.local import LocalRead
from app.schemas.palestrante import PalestranteRead
from app.schemas.participante import ParticipanteRead
from app.services.common import paginar

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Gestão de Eventos - TP02")
registrar_handlers(app)

@app.get("/eventos/", response_model=Page[EventoRead])
def listar_eventos(
    status: StatusEvento | None = None,
    tipo: TipoEvento | None = None,
    nome: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.Evento)
    if status:
        query = query.filter(models.Evento.status == status)
    if tipo:
        query = query.filter(models.Evento.tipo == tipo)
    if nome:
        query = query.filter(models.Evento.nome.ilike(f"%{nome}%"))
    return paginar(query, offset, limit)

@app.get("/locais/", response_model=Page[LocalRead])
def listar_locais(
    tipo: TipoLocal | None = None,
    ativo: bool | None = None,
    nome: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.Local)
    if tipo:
        query = query.filter(models.Local.tipo == tipo)
    if ativo is not None:
        query = query.filter(models.Local.ativo == ativo)
    if nome:
        query = query.filter(models.Local.nome.ilike(f"%{nome}%"))
    return paginar(query, offset, limit)

@app.post("/participantes/", response_model=schemas.ParticipanteResponse, status_code=status.HTTP_201_CREATED)
def criar_participante(participante: schemas.ParticipanteCreate, db: Session = Depends(get_db)):
    db_participante = models.Participante(**participante.model_dump())
    db.add(db_participante)
    db.commit()
    db.refresh(db_participante)
    return db_participante

@app.get("/participantes/", response_model=Page[ParticipanteRead])
def listar_participantes(
    nome: str | None = None,
    ativo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.Participante)
    if nome:
        query = query.filter(models.Participante.nome.ilike(f"%{nome}%"))
    if ativo is not None:
        query = query.filter(models.Participante.ativo == ativo)
    return paginar(query, offset, limit)

@app.get("/participantes/{participante_id}", response_model=schemas.ParticipanteResponse)
def obter_participante(participante_id: int, db: Session = Depends(get_db)):
    db_participante = db.query(models.Participante).filter(models.Participante.id == participante_id).first()
    if not db_participante:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participante não encontrado")
    return db_participante

@app.put("/participantes/{participante_id}", response_model=schemas.ParticipanteResponse)
def atualizar_participante(participante_id: int, participante: schemas.ParticipanteUpdate, db: Session = Depends(get_db)):
    db_participante = db.query(models.Participante).filter(models.Participante.id == participante_id).first()
    if not db_participante:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participante não encontrado")

    participante_data = participante.model_dump(exclude_unset=True)
    for key, value in participante_data.items():
        setattr(db_participante, key, value)

    db.commit()
    db.refresh(db_participante)
    return db_participante

@app.delete("/participantes/{participante_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_participante(participante_id: int, db: Session = Depends(get_db)):
    db_participante = db.query(models.Participante).filter(models.Participante.id == participante_id).first()
    if not db_participante:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participante não encontrado")
    db.delete(db_participante)
    db.commit()
    return None

@app.post("/palestrantes/", response_model=schemas.PalestranteResponse, status_code=status.HTTP_201_CREATED)
def criar_palestrante(palestrante: schemas.PalestranteCreate, db: Session = Depends(get_db)):
    db_palestrante = models.Palestrante(**palestrante.model_dump())
    db.add(db_palestrante)
    db.commit()
    db.refresh(db_palestrante)
    return db_palestrante

@app.get("/palestrantes/", response_model=Page[PalestranteRead])
def listar_palestrantes(
    nome: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.Palestrante)
    if nome:
        query = query.filter(models.Palestrante.nome.ilike(f"%{nome}%"))
    return paginar(query, offset, limit)

@app.get("/palestrantes/{palestrante_id}", response_model=schemas.PalestranteResponse)
def obter_palestrante(palestrante_id: int, db: Session = Depends(get_db)):
    db_palestrante = db.query(models.Palestrante).filter(models.Palestrante.id == palestrante_id).first()
    if not db_palestrante:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Palestrante não encontrado")
    return db_palestrante

@app.put("/palestrantes/{palestrante_id}", response_model=schemas.PalestranteResponse)
def atualizar_palestrante(palestrante_id: int, palestrante: schemas.PalestranteUpdate, db: Session = Depends(get_db)):
    db_palestrante = db.query(models.Palestrante).filter(models.Palestrante.id == palestrante_id).first()
    if not db_palestrante:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Palestrante não encontrado")

    palestrante_data = palestrante.model_dump(exclude_unset=True)
    for key, value in palestrante_data.items():
        setattr(db_palestrante, key, value)

    db.commit()
    db.refresh(db_palestrante)
    return db_palestrante

@app.delete("/palestrantes/{palestrante_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_palestrante(palestrante_id: int, db: Session = Depends(get_db)):
    db_palestrante = db.query(models.Palestrante).filter(models.Palestrante.id == palestrante_id).first()
    if not db_palestrante:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Palestrante não encontrado")
    db.delete(db_palestrante)
    db.commit()
    return None

@app.post("/atividades/", response_model=schemas.AtividadeResponse, status_code=status.HTTP_201_CREATED)
def criar_atividade(atividade: schemas.AtividadeCreate, db: Session = Depends(get_db)):
    db_local = db.query(models.Local).filter(models.Local.id == atividade.local_id).first()
    if not db_local or not db_local.ativo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Local inativo ou inexistente")

    db_evento = db.query(models.Evento).filter(models.Evento.id == atividade.evento_id).first()
    if not db_evento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado")

    if atividade.inicio.replace(tzinfo=None) < db_evento.data_inicio or atividade.fim.replace(tzinfo=None) > db_evento.data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A atividade deve ocorrer dentro do periodo do evento"
        )

    palestrantes_db = db.query(models.Palestrante).filter(models.Palestrante.id.in_(atividade.palestrantes_ids)).all()

    atividade_data = atividade.model_dump(exclude={"palestrantes_ids"})
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

@app.get("/atividades/{atividade_id}", response_model=schemas.AtividadeResponse)
def obter_atividade(atividade_id: int, db: Session = Depends(get_db)):
    db_atividade = db.query(models.Atividade).filter(models.Atividade.id == atividade_id).first()
    if not db_atividade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atividade não encontrada")
    return db_atividade

@app.put("/atividades/{atividade_id}", response_model=schemas.AtividadeResponse)
def atualizar_atividade(atividade_id: int, atividade: schemas.AtividadeUpdate, db: Session = Depends(get_db)):
    db_atividade = db.query(models.Atividade).filter(models.Atividade.id == atividade_id).first()
    if not db_atividade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atividade não encontrada")

    atividade_data = atividade.model_dump(exclude_unset=True)

    if "palestrantes_ids" in atividade_data:
        palestrantes_ids = atividade_data.pop("palestrantes_ids")
        palestrantes_db = db.query(models.Palestrante).filter(models.Palestrante.id.in_(palestrantes_ids)).all()
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

@app.post("/inscricoes/", response_model=schemas.InscricaoResponse, status_code=status.HTTP_201_CREATED)
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

@app.patch("/inscricoes/{inscricao_id}/status", response_model=schemas.InscricaoResponse)
def mudar_status_inscricao(inscricao_id: int, novo_status: str, db: Session = Depends(get_db)):
    db_inscricao = db.query(models.Inscricao).filter(models.Inscricao.id == inscricao_id).first()
    if not db_inscricao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada")

    db_inscricao.status = novo_status
    db.commit()
    db.refresh(db_inscricao)
    return db_inscricao