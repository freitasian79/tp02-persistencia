from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint, Column, ForeignKey, Index, String, Table, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StatusAtividade, TipoAtividade, enum_type

if TYPE_CHECKING:
    from app.models.evento import Evento
    from app.models.inscricao import Inscricao
    from app.models.local import Local
    from app.models.palestrante import Palestrante


# Tabela associativa N:N — Atividade x Palestrante
atividade_palestrante = Table(
    "atividade_palestrante",
    Base.metadata,
    Column("atividade_id", ForeignKey("atividades.id", ondelete="CASCADE"), primary_key=True),
    Column("palestrante_id", ForeignKey("palestrantes.id", ondelete="RESTRICT"), primary_key=True),
)


class Atividade(Base):
    __tablename__ = "atividades"
    __table_args__ = (
        CheckConstraint("fim > inicio", name="horario_valido"),
        CheckConstraint("capacidade > 0", name="capacidade_positiva"),
        UniqueConstraint("evento_id", "titulo"),
        Index("ix_atividades_local_inicio", "local_id", "inicio"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    evento_id: Mapped[int] = mapped_column(ForeignKey("eventos.id", ondelete="RESTRICT"))
    local_id: Mapped[int] = mapped_column(ForeignKey("locais.id", ondelete="RESTRICT"))
    titulo: Mapped[str] = mapped_column(String(200))
    descricao: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[TipoAtividade] = mapped_column(enum_type(TipoAtividade))
    inicio: Mapped[datetime]
    fim: Mapped[datetime]
    capacidade: Mapped[int]
    status: Mapped[StatusAtividade] = mapped_column(
        enum_type(StatusAtividade),
        default=StatusAtividade.AGENDADA,
        server_default=StatusAtividade.AGENDADA.value,
    )
    criado_em: Mapped[datetime] = mapped_column(server_default=func.now())
    atualizado_em: Mapped[datetime | None] = mapped_column(onupdate=func.now())

    evento: Mapped[Evento] = relationship(back_populates="atividades")
    local: Mapped[Local] = relationship(back_populates="atividades")
    palestrantes: Mapped[list[Palestrante]] = relationship(
        secondary=atividade_palestrante, back_populates="atividades"
    )
    inscricoes: Mapped[list[Inscricao]] = relationship(back_populates="atividade")