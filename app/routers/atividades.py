from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BadRequestError, BusinessRuleError, ConflictError
from app.models.atividade import Atividade
from app.models.enums import StatusAtividade, StatusEvento, StatusInscricao, TipoAtividade
from app.models.evento import Evento
from app.models.inscricao import Inscricao
from app.models.local import Local
from app.models.palestrante import Palestrante
from app.schemas.atividade import AtividadeCreate, AtividadeRead, AtividadeUpdate
from app.schemas.common import Page
from app.services.common import aplicar, campos_para_atualizar, obter_ou_404, paginar, salvar

router = APIRouter(prefix="/atividades", tags=["Atividades"])


def _buscar_palestrantes(db: Session, ids: list[int]) -> list[Palestrante]:
    if not ids:
        return []
    palestrantes = db.query(Palestrante).filter(Palestrante.id.in_(ids)).all()
    if len(palestrantes) != len(set(ids)):
        encontrados = {p.id for p in palestrantes}
        faltantes = sorted(set(ids) - encontrados)
        raise BadRequestError(f"Palestrante(s) não encontrado(s): {faltantes}.")
    return palestrantes


def _verificar_conflito_local(
    db: Session,
    local_id: int,
    inicio: datetime,
    fim: datetime,
    ignorar_id: int | None = None,
) -> None:
    query = db.query(Atividade).filter(
        Atividade.local_id == local_id,
        Atividade.status != StatusAtividade.CANCELADA,
        Atividade.inicio < fim,
        Atividade.fim > inicio,
    )
    if ignorar_id is not None:
        query = query.filter(Atividade.id != ignorar_id)
    conflito = query.first()
    if conflito:
        raise ConflictError(
            f"Conflito de horário neste local com a atividade '{conflito.titulo}'."
        )


def _contar_inscritos(db: Session, atividade_id: int) -> int:
    return (
        db.query(func.count(Inscricao.id))
        .filter(
            Inscricao.atividade_id == atividade_id,
            Inscricao.status != StatusInscricao.CANCELADA,
        )
        .scalar()
        or 0
    )


def _preencher_vagas(db: Session, atividade: Atividade) -> Atividade:
    ocupadas = _contar_inscritos(db, atividade.id)
    atividade.vagas_disponiveis = max(0, atividade.capacidade - ocupadas)
    return atividade


@router.post("/", response_model=AtividadeRead, status_code=status.HTTP_201_CREATED)
def criar_atividade(dados: AtividadeCreate, db: Session = Depends(get_db)):
    evento = obter_ou_404(db, Evento, dados.evento_id, "Evento")
    if evento.status != StatusEvento.ATIVO:
        raise BusinessRuleError("Só é possível cadastrar atividades em eventos ativos.")

    local = obter_ou_404(db, Local, dados.local_id, "Local")
    if not local.ativo:
        raise BusinessRuleError("O local informado está inativo.")

    if dados.capacidade > local.capacidade:
        raise BusinessRuleError(
            f"Capacidade da atividade ({dados.capacidade}) excede a do local ({local.capacidade})."
        )

    if dados.inicio.date() < evento.data_inicio or dados.fim.date() > evento.data_fim:
        raise BusinessRuleError("A atividade deve ocorrer dentro do período do evento.")

    _verificar_conflito_local(db, local.id, dados.inicio, dados.fim)
    palestrantes = _buscar_palestrantes(db, dados.palestrante_ids)

    atividade = Atividade(**dados.model_dump(exclude={"palestrante_ids"}))
    atividade.palestrantes = palestrantes
    db.add(atividade)
    salvar(db)
    db.refresh(atividade)
    return _preencher_vagas(db, atividade)


@router.get("/", response_model=Page[AtividadeRead])
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
    query = db.query(Atividade)
    if status is not None:
        query = query.filter(Atividade.status == status)
    if tipo is not None:
        query = query.filter(Atividade.tipo == tipo)
    if evento_id is not None:
        query = query.filter(Atividade.evento_id == evento_id)
    if local_id is not None:
        query = query.filter(Atividade.local_id == local_id)
    if nome:
        query = query.filter(Atividade.titulo.ilike(f"%{nome}%"))

    if com_vagas is not None:
        ocupadas = (
            db.query(func.count(Inscricao.id))
            .filter(
                Inscricao.atividade_id == Atividade.id,
                Inscricao.status != StatusInscricao.CANCELADA,
            )
            .correlate(Atividade)
            .scalar_subquery()
        )
        if com_vagas:
            query = query.filter(Atividade.capacidade > ocupadas)
        else:
            query = query.filter(Atividade.capacidade <= ocupadas)

    pagina = paginar(query.order_by(Atividade.inicio, Atividade.id), offset, limit)
    for atividade in pagina["items"]:
        qtd = sum(1 for i in atividade.inscricoes if i.status != StatusInscricao.CANCELADA)
        atividade.vagas_disponiveis = max(0, atividade.capacidade - qtd)
    return pagina


@router.get("/{atividade_id}", response_model=AtividadeRead)
def obter_atividade(atividade_id: int, db: Session = Depends(get_db)):
    atividade = obter_ou_404(db, Atividade, atividade_id, "Atividade")
    return _preencher_vagas(db, atividade)


@router.patch("/{atividade_id}", response_model=AtividadeRead)
def atualizar_atividade(
    atividade_id: int,
    dados: AtividadeUpdate,
    db: Session = Depends(get_db),
):
    atividade = obter_ou_404(db, Atividade, atividade_id, "Atividade")
    if atividade.status == StatusAtividade.CANCELADA:
        raise BusinessRuleError("Não é possível alterar uma atividade cancelada.")

    campos = campos_para_atualizar(
        dados, {"local_id", "titulo", "tipo", "inicio", "fim", "capacidade"}
    )
    campos.pop("motivo_alteracao", None)

    novo_local_id = campos.get("local_id", atividade.local_id)
    local = obter_ou_404(db, Local, novo_local_id, "Local")
    if "local_id" in campos and not local.ativo:
        raise BusinessRuleError("O local informado está inativo.")

    novo_inicio = campos.get("inicio", atividade.inicio)
    novo_fim = campos.get("fim", atividade.fim)
    if novo_fim <= novo_inicio:
        raise BadRequestError("fim deve ser posterior a inicio.")

    if (
        novo_inicio.date() < atividade.evento.data_inicio
        or novo_fim.date() > atividade.evento.data_fim
    ):
        raise BusinessRuleError("A atividade deve ocorrer dentro do período do evento.")

    nova_capacidade = campos.get("capacidade", atividade.capacidade)
    if nova_capacidade > local.capacidade:
        raise BusinessRuleError(
            f"Capacidade da atividade ({nova_capacidade}) excede a do local ({local.capacidade})."
        )

    ocupadas = _contar_inscritos(db, atividade.id)
    if nova_capacidade < ocupadas:
        raise BusinessRuleError(
            f"Capacidade não pode ser menor que o total de inscritos ativos ({ocupadas})."
        )

    if "local_id" in campos or "inicio" in campos or "fim" in campos:
        _verificar_conflito_local(db, novo_local_id, novo_inicio, novo_fim, ignorar_id=atividade.id)

    if "palestrante_ids" in campos:
        palestrante_ids = campos.pop("palestrante_ids") or []
        if len(set(palestrante_ids)) != len(palestrante_ids):
            raise BadRequestError("palestrante_ids contém valores repetidos.")
        atividade.palestrantes = _buscar_palestrantes(db, palestrante_ids)

    aplicar(atividade, campos)
    salvar(db)
    db.refresh(atividade)
    return _preencher_vagas(db, atividade)


@router.delete("/{atividade_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_atividade(atividade_id: int, db: Session = Depends(get_db)):
    atividade = obter_ou_404(db, Atividade, atividade_id, "Atividade")
    possui_inscricao = (
        db.query(Inscricao.id).filter(Inscricao.atividade_id == atividade_id).first()
    )
    if possui_inscricao:
        raise BusinessRuleError(
            "Atividade possui inscrições registradas e não pode ser removida."
        )
    atividade.palestrantes.clear()
    db.delete(atividade)
    salvar(db)
