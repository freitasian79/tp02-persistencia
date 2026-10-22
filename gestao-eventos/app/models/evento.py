from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StatusEvento, TipoEvento, enum_type

if TYPE_CHECKING:
    from app.models.atividade import Atividade


class Evento(Base):
    __tablename__ = "eventos"
    __table_args__ = (CheckConstraint("data_fim >= data_inicio", name="periodo_valido"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), unique=True)
    descricao: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[TipoEvento] = mapped_column(enum_type(TipoEvento))
    data_inicio: Mapped[date]
    data_fim: Mapped[date]
    organizador: Mapped[str | None] = mapped_column(String(150))
    status: Mapped[StatusEvento] = mapped_column(
        enum_type(StatusEvento), default=StatusEvento.ATIVO, server_default=StatusEvento.ATIVO.value
    )
    criado_em: Mapped[datetime] = mapped_column(server_default=func.now())

    # 1:N — a programação do evento
    atividades: Mapped[list[Atividade]] = relationship(
        back_populates="evento", order_by="Atividade.inicio"
    )