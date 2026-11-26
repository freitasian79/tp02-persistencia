from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.inscricao import Inscricao
from app.models.presenca import Presenca
from app.schemas.common import Page
from app.schemas.presenca import PresencaCreate, PresencaRead
from app.services.common import obter_ou_404, paginar, salvar
from app.services.inscricoes import registrar_presenca

router = APIRouter(prefix="/presencas", tags=["Presenças"])


@router.post("/", response_model=PresencaRead, status_code=status.HTTP_201_CREATED)
def criar_presenca(dados: PresencaCreate, db: Session = Depends(get_db)):
    return registrar_presenca(db, inscricao_id=dados.inscricao_id, metodo=dados.metodo)


@router.get("/", response_model=Page[PresencaRead])
def listar_presencas(
    inscricao_id: int | None = None,
    atividade_id: int | None = None,
    metodo: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Presenca)
    if inscricao_id is not None:
        query = query.filter(Presenca.inscricao_id == inscricao_id)
    if atividade_id is not None:
        query = query.join(Inscricao).filter(Inscricao.atividade_id == atividade_id)
    if metodo:
        query = query.filter(Presenca.metodo == metodo)
    return paginar(query.order_by(Presenca.id), offset, limit)


@router.get("/{presenca_id}", response_model=PresencaRead)
def obter_presenca(presenca_id: int, db: Session = Depends(get_db)):
    return obter_ou_404(db, Presenca, presenca_id, "Presença")


@router.delete("/{presenca_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_presenca(presenca_id: int, db: Session = Depends(get_db)):
    presenca = obter_ou_404(db, Presenca, presenca_id, "Presença")
    db.delete(presenca)
    salvar(db)
