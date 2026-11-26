from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BusinessRuleError
from app.models.palestrante import Palestrante
from app.schemas.common import Page
from app.schemas.palestrante import PalestranteCreate, PalestranteRead, PalestranteUpdate
from app.services.common import aplicar, campos_para_atualizar, obter_ou_404, paginar, salvar

router = APIRouter(prefix="/palestrantes", tags=["Palestrantes"])


@router.post("/", response_model=PalestranteRead, status_code=status.HTTP_201_CREATED)
def criar_palestrante(dados: PalestranteCreate, db: Session = Depends(get_db)):
    palestrante = Palestrante(**dados.model_dump())
    db.add(palestrante)
    salvar(db)
    db.refresh(palestrante)
    return palestrante


@router.get("/", response_model=Page[PalestranteRead])
def listar_palestrantes(
    nome: str | None = None,
    area_atuacao: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Palestrante)
    if nome:
        query = query.filter(Palestrante.nome.ilike(f"%{nome}%"))
    if area_atuacao:
        query = query.filter(Palestrante.area_atuacao.ilike(f"%{area_atuacao}%"))
    return paginar(query.order_by(Palestrante.id), offset, limit)


@router.get("/{palestrante_id}", response_model=PalestranteRead)
def obter_palestrante(palestrante_id: int, db: Session = Depends(get_db)):
    return obter_ou_404(db, Palestrante, palestrante_id, "Palestrante")


@router.patch("/{palestrante_id}", response_model=PalestranteRead)
def atualizar_palestrante(
    palestrante_id: int,
    dados: PalestranteUpdate,
    db: Session = Depends(get_db),
):
    palestrante = obter_ou_404(db, Palestrante, palestrante_id, "Palestrante")
    campos = campos_para_atualizar(dados, {"nome", "email"})
    aplicar(palestrante, campos)
    salvar(db)
    db.refresh(palestrante)
    return palestrante


@router.delete("/{palestrante_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_palestrante(palestrante_id: int, db: Session = Depends(get_db)):
    palestrante = obter_ou_404(db, Palestrante, palestrante_id, "Palestrante")
    if palestrante.atividades:
        raise BusinessRuleError(
            "Palestrante está vinculado a atividades e não pode ser removido."
        )
    db.delete(palestrante)
    salvar(db)
