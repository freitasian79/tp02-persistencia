from fastapi import FastAPI

from app.core.config import settings
from app.core.database import Base, engine
from app.core.exceptions import registrar_handlers
from app.routers import (
    atividades,
    consultas,
    eventos,
    inscricoes,
    locais,
    palestrantes,
    participantes,
    presencas,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
registrar_handlers(app)

app.include_router(locais.router)
app.include_router(eventos.router)
app.include_router(participantes.router)
app.include_router(palestrantes.router)
app.include_router(atividades.router)
app.include_router(inscricoes.router)
app.include_router(presencas.router)
app.include_router(consultas.router)
