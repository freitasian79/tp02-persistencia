from typing import Any, TypeVar

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.exceptions import (
    BadRequestError, ConflictError, NotFoundError, traduzir_integridade,
)

M = TypeVar("M", bound=Base)


def obter_ou_404(db: Session, modelo: type[M], id_: int, nome: str) -> M:
    obj = db.get(modelo, id_)
    if obj is None:
        raise NotFoundError(f"{nome} com id {id_} não encontrado(a).")
    return obj


def campos_para_atualizar(dados: BaseModel, obrigatorios: set[str]) -> dict[str, Any]:
    """Só considera campos enviados; impede anular campos obrigatórios."""
    campos = dados.model_dump(exclude_unset=True)
    if not campos:
        raise BadRequestError("Nenhum campo informado para atualização.")
    nulos = sorted(k for k, v in campos.items() if v is None and k in obrigatorios)
    if nulos:
        raise BadRequestError(f"Campo(s) não podem ser nulos: {', '.join(nulos)}.")
    return campos


def aplicar(obj: Base, campos: dict[str, Any]) -> None:
    for campo, valor in campos.items():
        setattr(obj, campo, valor)


def salvar(db: Session) -> None:
    """Commit com rollback garantido e tradução de erros de integridade."""
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(traduzir_integridade(exc)) from exc
    except Exception:
        db.rollback()
        raise