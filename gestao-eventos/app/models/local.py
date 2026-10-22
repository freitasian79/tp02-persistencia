from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TipoLocal, enum_type

if TYPE_CHECKING:
    from app.models.atividade import Atividade


class Local(Base):
    """Espaço físico (auditório, sala, laboratório) onde atividades acontecem."""

    __tablename__ = "locais"
    __table_args__ = (CheckConstraint("capacidade > 0", name="capacidade_positiva"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True)
    tipo: Mapped[TipoLocal] = mapped_column(enum_type(TipoLocal))
    capacidade: Mapped[int]
    localizacao: Mapped[str | None] = mapped_column(String(200))
    recursos: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(default=True, server_default=true())

    # 1:N — um local recebe várias atividades (em horários diferentes)
    atividades: Mapped[list[Atividade]] = relationship(back_populates="local")