from app.schemas.atividade import AtividadeCreate, AtividadeRead, AtividadeUpdate
from app.schemas.common import Mensagem, Page
from app.schemas.evento import (
    EventoCancelamento,
    EventoCreate,
    EventoRead,
    EventoUpdate,
)
from app.schemas.inscricao import (
    InscricaoCreate,
    InscricaoDetalhe,
    InscricaoRead,
    InscricaoStatusUpdate,
)
from app.schemas.local import LocalCreate, LocalRead, LocalUpdate
from app.schemas.palestrante import (
    PalestranteCreate,
    PalestranteRead,
    PalestranteUpdate,
)
from app.schemas.participante import (
    ParticipanteCreate,
    ParticipanteRead,
    ParticipanteUpdate,
)
from app.schemas.presenca import PresencaCreate, PresencaRead
from app.schemas.resumos import (
    AtividadeResumo,
    EventoResumo,
    LocalResumo,
    PalestranteResumo,
    ParticipanteResumo,
)

__all__ = [
    "AtividadeCreate",
    "AtividadeRead",
    "AtividadeResumo",
    "AtividadeUpdate",
    "EventoCancelamento",
    "EventoCreate",
    "EventoRead",
    "EventoResumo",
    "EventoUpdate",
    "InscricaoCreate",
    "InscricaoDetalhe",
    "InscricaoRead",
    "InscricaoStatusUpdate",
    "LocalCreate",
    "LocalRead",
    "LocalResumo",
    "LocalUpdate",
    "Mensagem",
    "Page",
    "PalestranteCreate",
    "PalestranteRead",
    "PalestranteResumo",
    "PalestranteUpdate",
    "ParticipanteCreate",
    "ParticipanteRead",
    "ParticipanteResumo",
    "ParticipanteUpdate",
    "PresencaCreate",
    "PresencaRead",
]
