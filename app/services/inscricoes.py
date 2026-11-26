from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.atividade import Atividade
from app.models.enums import StatusInscricao
from app.models.inscricao import Inscricao
from app.models.participante import Participante
from app.models.presenca import Presenca


class BusinessRuleError(Exception):
    """Erro de regra de negócio (será mapeado para HTTP 400/409 na Issue #6)."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def contar_vagas_ocupadas(db: Session, atividade_id: int) -> int:
    stmt = (
        select(func.count(Inscricao.id))
        .where(
            Inscricao.atividade_id == atividade_id,
            Inscricao.status != StatusInscricao.CANCELADA,
        )
    )
    return db.scalar(stmt) or 0


def inscrever_participante(
    db: Session,
    *,
    participante_id: int,
    atividade_id: int,
    observacao: str | None = None,
) -> Inscricao:
    participante = db.get(Participante, participante_id)
    if not participante:
        raise BusinessRuleError("Participante não encontrado.", status_code=404)

    atividade = db.get(Atividade, atividade_id)
    if not atividade:
        raise BusinessRuleError("Atividade não encontrada.", status_code=404)

    # Regra 1: Impedir inscrição duplicada
    ja_inscrito = db.scalar(
        select(Inscricao).where(
            Inscricao.participante_id == participante_id,
            Inscricao.atividade_id == atividade_id,
        )
    )
    if ja_inscrito:
        raise BusinessRuleError(
            "Participante já possui inscrição nesta atividade.",
            status_code=409,
        )

    # Regra 2 (F17): Controle de limite de vagas da atividade
    ocupadas = contar_vagas_ocupadas(db, atividade_id)
    if ocupadas >= atividade.vagas_maximas:
        raise BusinessRuleError(
            f"Atividade lotada ({ocupadas}/{atividade.vagas_maximas} vagas ocupadas).",
            status_code=409,
        )

    inscricao = Inscricao(
        participante_id=participante_id,
        atividade_id=atividade_id,
        status=StatusInscricao.CONFIRMADA,
        observacao=observacao,
    )
    db.add(inscricao)
    db.commit()
    db.refresh(inscricao)
    return inscricao


def registrar_presenca(
    db: Session,
    *,
    inscricao_id: int,
    metodo: str = "manual",
) -> Presenca:
    inscricao = db.get(Inscricao, inscricao_id)
    if not inscricao:
        raise BusinessRuleError("Inscrição não encontrada.", status_code=404)

    # Regra 3: Não permitir check-in em inscrição cancelada
    if inscricao.status == StatusInscricao.CANCELADA:
        raise BusinessRuleError(
            "Não é possível registrar presença para uma inscrição cancelada.",
            status_code=400,
        )

    if inscricao.presenca is not None:
        raise BusinessRuleError(
            "Presença já registrada para esta inscrição.",
            status_code=409,
        )

    presenca = Presenca(inscricao_id=inscricao_id, metodo=metodo)
    db.add(presenca)
    db.commit()
    db.refresh(presenca)
    return presenca