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

@app.get("/palestrantes/", response_model=List[schemas.PalestranteResponse])
def listar_palestrantes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Palestrante).offset(skip).limit(limit).all()

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
    palestrantes_db = db.query(models.Palestrante).filter(models.Palestrante.id.in_(atividade.palestrantes_ids)).all()
    
    atividade_data = atividade.model_dump(exclude={"palestrantes_ids"})
    db_atividade = models.Atividade(**atividade_data)
    db_atividade.palestrantes = palestrantes_db
    
    db.add(db_atividade)
    db.commit()
    db.refresh(db_atividade)
    return db_atividade

@app.get("/atividades/", response_model=List[schemas.AtividadeResponse])
def listar_atividades(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Atividade).offset(skip).limit(limit).all()

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