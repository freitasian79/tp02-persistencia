from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BusinessRuleError
from app.models.atividade import Atividade
from app.models.enums import StatusAtividade, TipoLocal
from app.models.local import Local
from app.schemas.common import Page
from app.schemas.local import LocalCreate, LocalRead, LocalUpdate
from app.services.common import aplicar, campos_para_atualizar, obter_ou_404, paginar, salvar

router = APIRouter(prefix="/locais", tags=["Locais"])


@router.post("/", response_model=LocalRead, status_code=status.HTTP_201_CREATED)
def criar_local(dados: LocalCreate, db: Session = Depends(get_db)):
    local = Local(**dados.model_dump())
    db.add(local)
    salvar(db)
    db.refresh(local)
    return local


@router.get("/", response_model=Page[LocalRead])
def listar_locais(
    tipo: TipoLocal | None = None,
    ativo: bool | None = None,
    nome: str | None = None,
    capacidade_min: int | None = Query(default=None, ge=1),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Local)
    if tipo is not None:
        query = query.filter(Local.tipo == tipo)
    if ativo is not None:
        query = query.filter(Local.ativo == ativo)
    if nome:
        query = query.filter(Local.nome.ilike(f"%{nome}%"))
    if capacidade_min is not None:
        query = query.filter(Local.capacidade >= capacidade_min)
    return paginar(query.order_by(Local.id), offset, limit)


@router.get("/{local_id}", response_model=LocalRead)
def obter_local(local_id: int, db: Session = Depends(get_db)):
    return obter_ou_404(db, Local, local_id, "Local")


@router.patch("/{local_id}", response_model=LocalRead)
def atualizar_local(local_id: int, dados: LocalUpdate, db: Session = Depends(get_db)):
    local = obter_ou_404(db, Local, local_id, "Local")
    campos = campos_para_atualizar(dados, {"nome", "tipo", "capacidade", "ativo"})

    if "capacidade" in campos:
        conflito = (
            db.query(Atividade)
            .filter(
                Atividade.local_id == local.id,
                Atividade.status != StatusAtividade.CANCELADA,
                Atividade.capacidade > campos["capacidade"],
            )
            .first()
        )
        if conflito:
            raise BusinessRuleError(
                "Existem atividades neste local com capacidade maior que a informada."
            )

    aplicar(local, campos)
    salvar(db)
    db.refresh(local)
    return local


@router.delete("/{local_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_local(local_id: int, db: Session = Depends(get_db)):
    local = obter_ou_404(db, Local, local_id, "Local")
    possui_atividade = db.query(Atividade.id).filter(Atividade.local_id == local_id).first()
    if possui_atividade:
        raise BusinessRuleError(
            "Local possui atividades vinculadas e não pode ser removido; desative-o em vez de excluir."
        )
    db.delete(local)
    salvar(db)
