from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.inscricao import Inscricao


class Presenca(Base):
    """Check-in do participante na atividade (1:1 com Inscricao)."""

    __tablename__ = "presencas"

    id: Mapped[int] = mapped_column(primary_key=True)
    inscricao_id: Mapped[int] = mapped_column(
        ForeignKey("inscricoes.id", ondelete="CASCADE"), unique=True
    )
    registrada_em: Mapped[datetime] = mapped_column(server_default=func.now())
    metodo: Mapped[str] = mapped_column(String(20), default="manual", server_default="manual")

    inscricao: Mapped[Inscricao] = relationship(back_populates="presenca")