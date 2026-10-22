from enum import Enum

from sqlalchemy import Enum as SAEnum


class TipoEvento(str, Enum):
    CONGRESSO = "congresso"
    SEMINARIO = "seminario"
    SIMPOSIO = "simposio"
    WORKSHOP = "workshop"
    OUTRO = "outro"


class StatusEvento(str, Enum):
    ATIVO = "ativo"
    CANCELADO = "cancelado"
    ENCERRADO = "encerrado"


class TipoLocal(str, Enum):
    AUDITORIO = "auditorio"
    SALA = "sala"
    LABORATORIO = "laboratorio"
    OUTRO = "outro"


class TipoAtividade(str, Enum):
    PALESTRA = "palestra"
    OFICINA = "oficina"
    MINICURSO = "minicurso"
    MESA_REDONDA = "mesa_redonda"


class StatusAtividade(str, Enum):
    AGENDADA = "agendada"
    CANCELADA = "cancelada"
    CONCLUIDA = "concluida"


class StatusInscricao(str, Enum):
    PENDENTE = "pendente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"


def enum_type(enum_cls: type[Enum]) -> SAEnum:
    """Enum salvo como VARCHAR (portável entre PostgreSQL e SQLite), gravando o .value."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=20,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )