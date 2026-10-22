from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StatusInscricao, enum_type

if TYPE_CHECKING:
    from app.models.atividade import Atividade
    from app.models.participante import Participante
    from app.models.presenca import Presenca


class Inscricao(Base):
    """Associação N:N Participante x Atividade, com status próprio."""

    __tablename__ = "inscricoes"
    __table_args__ = (
        UniqueConstraint("participante_id", "atividade_id"),  # impede duplicidade
        Index("ix_inscricoes_atividade_status", "atividade_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    participante_id: Mapped[int] = mapped_column(ForeignKey("participantes.id", ondelete="RESTRICT"))
    atividade_id: Mapped[int] = mapped_column(ForeignKey("atividades.id", ondelete="RESTRICT"))
    status: Mapped[StatusInscricao] = mapped_column(
        enum_type(StatusInscricao),
        default=StatusInscricao.PENDENTE,
        server_default=StatusInscricao.PENDENTE.value,
    )
    data_inscricao: Mapped[datetime] = mapped_column(server_default=func.now())
    atualizada_em: Mapped[datetime | None] = mapped_column(onupdate=func.now())
    observacao: Mapped[str | None] = mapped_column(String(255))

    participante: Mapped[Participante] = relationship(back_populates="inscricoes")
    atividade: Mapped[Atividade] = relationship(back_populates="inscricoes")
    # 1:1 — cada inscrição tem no máximo um registro de presença
    presenca: Mapped[Presenca | None] = relationship(
        back_populates="inscricao", uselist=False, cascade="all, delete-orphan"
    )