from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError
from app.models.atividade import Atividade
from app.models.enums import StatusAtividade, StatusEvento, StatusInscricao
from app.models.inscricao import Inscricao
from app.models.participante import Participante
from app.models.presenca import Presenca
from app.services.common import obter_ou_404, salvar


def contar_vagas_ocupadas(db: Session, atividade_id: int) -> int:
    stmt = select(func.count(Inscricao.id)).where(
        Inscricao.atividade_id == atividade_id,
        Inscricao.status != StatusInscricao.CANCELADA,
    )
    return db.scalar(stmt) or 0


def inscrever_participante(
    db: Session,
    *,
    participante_id: int,
    atividade_id: int,
    observacao: str | None = None,
) -> Inscricao:
    participante = obter_ou_404(db, Participante, participante_id, "Participante")
    if not participante.ativo:
        raise BusinessRuleError("Participante inativo não pode realizar inscrição.")

    atividade = obter_ou_404(db, Atividade, atividade_id, "Atividade")
    if atividade.status == StatusAtividade.CANCELADA:
        raise BusinessRuleError("Não é possível se inscrever em uma atividade cancelada.")
    if atividade.evento.status != StatusEvento.ATIVO:
        raise BusinessRuleError("Não é possível se inscrever em atividades de evento inativo.")

    existente = db.scalar(
        select(Inscricao).where(
            Inscricao.participante_id == participante_id,
            Inscricao.atividade_id == atividade_id,
        )
    )
    if existente and existente.status != StatusInscricao.CANCELADA:
        raise ConflictError("Participante já possui inscrição ativa nesta atividade.")

    ocupadas = contar_vagas_ocupadas(db, atividade_id)
    if ocupadas >= atividade.capacidade:
        raise ConflictError(
            f"Atividade lotada ({ocupadas}/{atividade.capacidade} vagas ocupadas)."
        )

    if existente and existente.status == StatusInscricao.CANCELADA:
        existente.status = StatusInscricao.CONFIRMADA
        if observacao is not None:
            existente.observacao = observacao
        salvar(db)
        db.refresh(existente)
        return existente

    inscricao = Inscricao(
        participante_id=participante_id,
        atividade_id=atividade_id,
        status=StatusInscricao.CONFIRMADA,
        observacao=observacao,
    )
    db.add(inscricao)
    salvar(db)
    db.refresh(inscricao)
    return inscricao


def atualizar_status_inscricao(
    db: Session,
    *,
    inscricao_id: int,
    novo_status: StatusInscricao,
    observacao: str | None = None,
) -> Inscricao:
    inscricao = obter_ou_404(db, Inscricao, inscricao_id, "Inscrição")

    if novo_status == StatusInscricao.CANCELADA and inscricao.presenca is not None:
        raise BusinessRuleError(
            "Não é possível cancelar inscrição que já possui presença registrada."
        )

    if (
        inscricao.status == StatusInscricao.CANCELADA
        and novo_status != StatusInscricao.CANCELADA
    ):
        ocupadas = contar_vagas_ocupadas(db, inscricao.atividade_id)
        if ocupadas >= inscricao.atividade.capacidade:
            raise ConflictError("Atividade sem vagas disponíveis para reativar a inscrição.")

    inscricao.status = novo_status
    if observacao is not None:
        inscricao.observacao = observacao
    salvar(db)
    db.refresh(inscricao)
    return inscricao


def registrar_presenca(
    db: Session,
    *,
    inscricao_id: int,
    metodo: str = "manual",
) -> Presenca:
    inscricao = obter_ou_404(db, Inscricao, inscricao_id, "Inscrição")

    if not inscricao.participante.ativo:
        raise BusinessRuleError("Participante inativo.")
    if inscricao.status != StatusInscricao.CONFIRMADA:
        raise BusinessRuleError("Apenas inscrições confirmadas podem registrar presença.")
    if inscricao.atividade.status == StatusAtividade.CANCELADA:
        raise BusinessRuleError("Não é possível registrar presença em atividade cancelada.")
    if inscricao.presenca is not None:
        raise ConflictError("Presença já registrada para esta inscrição.")

    presenca = Presenca(inscricao_id=inscricao_id, metodo=metodo)
    db.add(presenca)
    salvar(db)
    db.refresh(presenca)
    return presenca
