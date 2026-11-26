from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


def paginate(db: Session, stmt: Select, offset: int, limit: int) -> dict:
    """Aplica OFFSET/LIMIT na própria consulta SQL (não recorta em memória)."""
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    items = db.scalars(stmt.offset(offset).limit(limit)).all()
    return {"items": items, "total": total or 0, "offset": offset, "limit": limit}