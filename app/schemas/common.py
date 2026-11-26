from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    offset: int
    limit: int


class Mensagem(BaseModel):
    detail: str


def para_naive(valor: datetime | None) -> datetime | None:
    """Remove fuso para comparar horários de forma consistente no PostgreSQL e no SQLite."""
    if valor is not None and valor.tzinfo is not None:
        return valor.replace(tzinfo=None)
    return valor