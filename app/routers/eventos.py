from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BadRequestError, BusinessRuleError
from app.models.atividade import Atividade
from app.models.enums import StatusAtividade, StatusEvento, StatusInscricao, TipoEvento
from app.models.evento import Evento
from app.models.inscricao import Inscricao
from app.schemas.common import Page
from app.schemas.evento import EventoCancelamento, EventoCreate, EventoRead, EventoUpdate
from app.services.common import aplicar, campos_para_atualizar, obter_ou_404, paginar, salvar

router = APIRouter(prefix="/eventos", tags=["Eventos"])


@router.post("/", response_model=EventoRead, status_code=status.HTTP_201_CREATED)
def criar_evento(dados: EventoCreate, db: Session = Depends(get_db)):
    evento = Evento(**dados.model_dump())
    db.add(evento)
    salvar(db)
    db.refresh(evento)
    return evento


@router.get("/", response_model=Page[EventoRead])
def listar_eventos(
    status: StatusEvento | None = None,
    tipo: TipoEvento | None = None,
    nome: str | None = None,
    data_de: date | None = None,
    data_ate: date | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Evento)
    if status is not None:
        query = query.filter(Evento.status == status)
    if tipo is not None:
        query = query.filter(Evento.tipo == tipo)
    if nome:
        query = query.filter(Evento.nome.ilike(f"%{nome}%"))
    if data_de is not None:
        query = query.filter(Evento.data_fim >= data_de)
    if data_ate is not None:
        query = query.filter(Evento.data_inicio <= data_ate)
    return paginar(query.order_by(Evento.data_inicio, Evento.id), offset, limit)


@router.get("/{evento_id}", response_model=EventoRead)
def obter_evento(evento_id: int, db: Session = Depends(get_db)):
    return obter_ou_404(db, Evento, evento_id, "Evento")


@router.patch("/{evento_id}", response_model=EventoRead)
def atualizar_evento(evento_id: int, dados: EventoUpdate, db: Session = Depends(get_db)):
    evento = obter_ou_404(db, Evento, evento_id, "Evento")
    if evento.status == StatusEvento.CANCELADO:
        raise BusinessRuleError("Não é possível alterar um evento cancelado.")

    campos = campos_para_atualizar(dados, {"nome", "tipo", "data_inicio", "data_fim"})
    nova_inicio = campos.get("data_inicio", evento.data_inicio)
    nova_fim = campos.get("data_fim", evento.data_fim)
    if nova_fim < nova_inicio:
        raise BadRequestError("data_fim deve ser igual ou posterior a data_inicio.")

    if "data_inicio" in campos or "data_fim" in campos:
        for atv in evento.atividades:
            if atv.status == StatusAtividade.CANCELADA:
                continue
            if atv.inicio.date() < nova_inicio or atv.fim.date() > nova_fim:
                raise BusinessRuleError(
                    f"A atividade '{atv.titulo}' ficaria fora do novo período do evento."
                )

    aplicar(evento, campos)
    salvar(db)
    db.refresh(evento)
    return evento


@router.post("/{evento_id}/cancelar", response_model=EventoCancelamento)
def cancelar_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = obter_ou_404(db, Evento, evento_id, "Evento")
    if evento.status == StatusEvento.CANCELADO:
        raise BusinessRuleError("Este evento já está cancelado.")

    evento.status = StatusEvento.CANCELADO
    atividades_canceladas = 0
    inscricoes_canceladas = 0

    for atividade in evento.atividades:
        if atividade.status != StatusAtividade.CANCELADA:
            atividade.status = StatusAtividade.CANCELADA
            atividades_canceladas += 1

        inscricoes = (
            db.query(Inscricao)
            .filter(
                Inscricao.atividade_id == atividade.id,
                Inscricao.status != StatusInscricao.CANCELADA,
            )
            .all()
        )
        for insc in inscricoes:
            insc.status = StatusInscricao.CANCELADA
            inscricoes_canceladas += 1

    salvar(db)
    return EventoCancelamento(
        evento_id=evento.id,
        status=evento.status,
        atividades_canceladas=atividades_canceladas,
        inscricoes_canceladas=inscricoes_canceladas,
    )


@router.delete("/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = obter_ou_404(db, Evento, evento_id, "Evento")
    possui_atividade = db.query(Atividade.id).filter(Atividade.evento_id == evento_id).first()
    if possui_atividade:
        raise BusinessRuleError(
            "Evento possui atividades cadastradas e não pode ser removido."
        )
    db.delete(evento)
    salvar(db)
