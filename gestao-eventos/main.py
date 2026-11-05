from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.database import get_db, engine 

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Gestão de Eventos - TP02")

@app.post("/participantes/", response_model=schemas.ParticipanteResponse, status_code=status.HTTP_201_CREATED)
def criar_participante(participante: schemas.ParticipanteCreate, db: Session = Depends(get_db)):
    db_participante = models.Participante(**participante.model_dump())
    db.add(db_participante)
    db.commit()
    db.refresh(db_participante)
    return db_participante

@app.get("/participantes/", response_model=List[schemas.ParticipanteResponse])
def listar_participantes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Participante).offset(skip).limit(limit).all()

@app.get("/participantes/{participante_id}", response_model=schemas.ParticipanteResponse)
def obter_participante(participante_id: int, db: Session = Depends(get_db)):
    participante = db.query(models.Participante).filter(models.Participante.id == participante_id).first()
    if not participante:
        raise HTTPException(status_code=404, detail="Participante não encontrado")
    return participante

@app.patch("/participantes/{participante_id}/desativar", response_model=schemas.ParticipanteResponse)
def desativar_participante(participante_id: int, db: Session = Depends(get_db)):
    participante = db.query(models.Participante).filter(models.Participante.id == participante_id).first()
    if not participante:
        raise HTTPException(status_code=404, detail="Participante não encontrado")
    
    participante.ativo = False
    db.commit()
    db.refresh(participante)
    return participante

@app.post("/palestrantes/", response_model=schemas.PalestranteResponse, status_code=status.HTTP_201_CREATED)
def criar_palestrante(palestrante: schemas.PalestranteCreate, db: Session = Depends(get_db)):
    db_palestrante = models.Palestrante(**palestrante.model_dump())
    db.add(db_palestrante)
    db.commit()
    db.refresh(db_palestrante)
    return db_palestrante

@app.get("/palestrantes/", response_model=List[schemas.PalestranteResponse])
def listar_palestrantes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Palestrante).offset(skip).limit(limit).all()

@app.get("/palestrantes/{palestrante_id}", response_model=schemas.PalestranteResponse)
def obter_palestrante(palestrante_id: int, db: Session = Depends(get_db)):
    palestrante = db.query(models.Palestrante).filter(models.Palestrante.id == palestrante_id).first()
    if not palestrante:
        raise HTTPException(status_code=404, detail="Palestrante não encontrado")
    return palestrante