from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.atividade import Atividade
from app.models.enums import StatusInscricao
from app.models.inscricao import Inscricao
from app.schemas.common import Page
from app.schemas.inscricao import (
    InscricaoCreate,
    InscricaoDetalhe,
    InscricaoRead,
    InscricaoStatusUpdate,
)
from app.schemas.presenca import PresencaRead
from app.services.common import obter_ou_404, paginar, salvar
from app.services.inscricoes import atualizar_status_inscricao, inscrever_participante

router = APIRouter(prefix="/inscricoes", tags=["Inscrições"])


@router.post("/", response_model=InscricaoDetalhe, status_code=status.HTTP_201_CREATED)
def criar_inscricao(dados: InscricaoCreate, db: Session = Depends(get_db)):
    return inscrever_participante(
        db,
        participante_id=dados.participante_id,
        atividade_id=dados.atividade_id,
        observacao=dados.observacao,
    )


@router.get("/", response_model=Page[InscricaoRead])
def listar_inscricoes(
    status: StatusInscricao | None = None,
    participante_id: int | None = None,
    atividade_id: int | None = None,
    evento_id: int | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Inscricao)
    if status is not None:
        query = query.filter(Inscricao.status == status)
    if participante_id is not None:
        query = query.filter(Inscricao.participante_id == participante_id)
    if atividade_id is not None:
        query = query.filter(Inscricao.atividade_id == atividade_id)
    if evento_id is not None:
        query = query.join(Atividade).filter(Atividade.evento_id == evento_id)
    return paginar(query.order_by(Inscricao.id), offset, limit)


@router.get("/{inscricao_id}", response_model=InscricaoDetalhe)
def obter_inscricao(inscricao_id: int, db: Session = Depends(get_db)):
    return obter_ou_404(db, Inscricao, inscricao_id, "Inscrição")


@router.patch("/{inscricao_id}/status", response_model=InscricaoRead)
def mudar_status_inscricao(
    inscricao_id: int,
    dados: InscricaoStatusUpdate,
    db: Session = Depends(get_db),
):
    return atualizar_status_inscricao(
        db,
        inscricao_id=inscricao_id,
        novo_status=dados.status,
        observacao=dados.observacao,
    )


@router.get("/{inscricao_id}/presenca", response_model=PresencaRead)
def obter_presenca_inscricao(inscricao_id: int, db: Session = Depends(get_db)):
    inscricao = obter_ou_404(db, Inscricao, inscricao_id, "Inscrição")
    if inscricao.presenca is None:
        raise NotFoundError("Presença ainda não registrada para esta inscrição.")
    return inscricao.presenca


@router.delete("/{inscricao_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_inscricao(inscricao_id: int, db: Session = Depends(get_db)):
    inscricao = obter_ou_404(db, Inscricao, inscricao_id, "Inscrição")
    if inscricao.presenca is not None:
        raise BusinessRuleError(
            "Inscrição já possui presença registrada e não pode ser removida."
        )
    db.delete(inscricao)
    salvar(db)
