from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.inscricao import Inscricao


class Participante(Base):
    __tablename__ = "participantes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    cpf: Mapped[str] = mapped_column(String(11), unique=True)
    telefone: Mapped[str | None] = mapped_column(String(20))
    instituicao: Mapped[str | None] = mapped_column(String(150))
    ativo: Mapped[bool] = mapped_column(default=True, server_default=true())
    criado_em: Mapped[datetime] = mapped_column(server_default=func.now())

    # N:N com Atividade, via objeto associativo Inscricao
    inscricoes: Mapped[list[Inscricao]] = relationship(back_populates="participante")