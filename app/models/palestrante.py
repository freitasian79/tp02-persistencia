from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.atividade import Atividade


class Palestrante(Base):
    __tablename__ = "palestrantes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    area_atuacao: Mapped[str | None] = mapped_column(String(120))
    mini_bio: Mapped[str | None] = mapped_column(Text)

    # N:N — um palestrante conduz várias atividades
    atividades: Mapped[list[Atividade]] = relationship(
        secondary="atividade_palestrante", back_populates="palestrantes"
    )