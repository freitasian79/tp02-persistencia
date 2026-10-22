from app.models.atividade import Atividade, atividade_palestrante
from app.models.evento import Evento
from app.models.inscricao import Inscricao
from app.models.local import Local
from app.models.palestrante import Palestrante
from app.models.participante import Participante
from app.models.presenca import Presenca

__all__ = [
    "Atividade", "atividade_palestrante", "Evento", "Inscricao",
    "Local", "Palestrante", "Participante", "Presenca",
]