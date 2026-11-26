from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import StatusAtividade, StatusInscricao, TipoAtividade
from app.schemas.resumos import AtividadeResumo, ParticipanteResumo


class ItemProgramacao(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inscricao_id: int
    status_inscricao: StatusInscricao
    presente: bool
    atividade: AtividadeResumo


class ProgramacaoParticipante(BaseModel):
    participante: ParticipanteResumo
    atividades: list[ItemProgramacao]


class OcupacaoAtividade(BaseModel):
    atividade_id: int
    titulo: str
    tipo: TipoAtividade
    status: StatusAtividade
    inicio: datetime
    fim: datetime
    evento_nome: str
    local_nome: str
    capacidade: int
    inscritos_ativos: int
    vagas_disponiveis: int
    total_presencas: int
    ocupacao_percentual: float


class ContagemGrupo(BaseModel):
    chave: str
    quantidade: int


class ResumoEventoEstatistica(BaseModel):
    evento_id: int
    evento_nome: str
    total_atividades: int
    total_inscricoes_ativas: int


class EstatisticasGerais(BaseModel):
    total_eventos: int
    total_locais_ativos: int
    total_participantes_ativos: int
    total_palestrantes: int
    total_atividades: int
    total_inscricoes_ativas: int
    total_presencas: int
    capacidade_total_atividades: int
    media_capacidade_atividade: float
    taxa_ocupacao_percentual: float
    taxa_presenca_percentual: float
    atividades_por_tipo: list[ContagemGrupo]
    inscricoes_por_status: list[ContagemGrupo]
    resumo_por_evento: list[ResumoEventoEstatistica]
