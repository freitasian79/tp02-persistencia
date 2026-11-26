from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BusinessRuleError
from app.models.inscricao import Inscricao
from app.models.participante import Participante
from app.schemas.common import Page
from app.schemas.participante import ParticipanteCreate, ParticipanteRead, ParticipanteUpdate
from app.services.common import aplicar, campos_para_atualizar, obter_ou_404, paginar, salvar

router = APIRouter(prefix="/participantes", tags=["Participantes"])


@router.post("/", response_model=ParticipanteRead, status_code=status.HTTP_201_CREATED)
def criar_participante(dados: ParticipanteCreate, db: Session = Depends(get_db)):
    participante = Participante(**dados.model_dump())
    db.add(participante)
    salvar(db)
    db.refresh(participante)
    return participante


@router.get("/", response_model=Page[ParticipanteRead])
def listar_participantes(
    nome: str | None = None,
    ativo: bool | None = None,
    instituicao: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Participante)
    if nome:
        query = query.filter(Participante.nome.ilike(f"%{nome}%"))
    if ativo is not None:
        query = query.filter(Participante.ativo == ativo)
    if instituicao:
        query = query.filter(Participante.instituicao.ilike(f"%{instituicao}%"))
    return paginar(query.order_by(Participante.id), offset, limit)


@router.get("/{participante_id}", response_model=ParticipanteRead)
def obter_participante(participante_id: int, db: Session = Depends(get_db)):
    return obter_ou_404(db, Participante, participante_id, "Participante")


@router.patch("/{participante_id}", response_model=ParticipanteRead)
def atualizar_participante(
    participante_id: int,
    dados: ParticipanteUpdate,
    db: Session = Depends(get_db),
):
    participante = obter_ou_404(db, Participante, participante_id, "Participante")
    campos = campos_para_atualizar(dados, {"nome", "email", "ativo"})
    aplicar(participante, campos)
    salvar(db)
    db.refresh(participante)
    return participante


@router.delete("/{participante_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_participante(participante_id: int, db: Session = Depends(get_db)):
    participante = obter_ou_404(db, Participante, participante_id, "Participante")
    possui_inscricao = (
        db.query(Inscricao.id).filter(Inscricao.participante_id == participante_id).first()
    )
    if possui_inscricao:
        raise BusinessRuleError(
            "Participante possui inscrições registradas e não pode ser removido; desative o cadastro."
        )
    db.delete(participante)
    salvar(db)
