from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.atividade import Atividade, atividade_palestrante
from app.models.enums import StatusInscricao, TipoAtividade
from app.models.evento import Evento
from app.models.inscricao import Inscricao
from app.models.local import Local
from app.models.palestrante import Palestrante
from app.models.participante import Participante
from app.models.presenca import Presenca
from app.schemas.atividade import AtividadeRead
from app.schemas.common import Page
from app.schemas.consultas import (
    ContagemGrupo,
    EstatisticasGerais,
    ItemProgramacao,
    OcupacaoAtividade,
    ProgramacaoParticipante,
    ResumoEventoEstatistica,
)
from app.schemas.inscricao import InscricaoDetalhe
from app.services.common import obter_ou_404, paginar

router = APIRouter(tags=["Consultas e Estatísticas"])


@router.get("/eventos/{evento_id}/atividades", response_model=Page[AtividadeRead])
def listar_atividades_do_evento(
    evento_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    obter_ou_404(db, Evento, evento_id, "Evento")
    query = (
        db.query(Atividade)
        .filter(Atividade.evento_id == evento_id)
        .order_by(Atividade.inicio.asc(), Atividade.id.asc())
    )
    pagina = paginar(query, offset, limit)
    for atividade in pagina["items"]:
        qtd = sum(1 for i in atividade.inscricoes if i.status != StatusInscricao.CANCELADA)
        atividade.vagas_disponiveis = max(0, atividade.capacidade - qtd)
    return pagina


@router.get("/palestrantes/{palestrante_id}/atividades", response_model=list[AtividadeRead])
def listar_atividades_do_palestrante(palestrante_id: int, db: Session = Depends(get_db)):
    obter_ou_404(db, Palestrante, palestrante_id, "Palestrante")
    atividades = (
        db.query(Atividade)
        .join(atividade_palestrante, Atividade.id == atividade_palestrante.c.atividade_id)
        .filter(atividade_palestrante.c.palestrante_id == palestrante_id)
        .order_by(Atividade.inicio.asc())
        .all()
    )
    for atividade in atividades:
        qtd = sum(1 for i in atividade.inscricoes if i.status != StatusInscricao.CANCELADA)
        atividade.vagas_disponiveis = max(0, atividade.capacidade - qtd)
    return atividades


@router.get("/atividades/{atividade_id}/inscricoes", response_model=Page[InscricaoDetalhe])
def listar_inscricoes_da_atividade(
    atividade_id: int,
    status: StatusInscricao | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    obter_ou_404(db, Atividade, atividade_id, "Atividade")
    query = db.query(Inscricao).filter(Inscricao.atividade_id == atividade_id)
    if status is not None:
        query = query.filter(Inscricao.status == status)
    return paginar(query.order_by(Inscricao.data_inscricao.asc()), offset, limit)


@router.get("/participantes/{participante_id}/programacao", response_model=ProgramacaoParticipante)
def obter_programacao_participante(
    participante_id: int,
    evento_id: int | None = None,
    inicio_de: datetime | None = None,
    inicio_ate: datetime | None = None,
    db: Session = Depends(get_db),
):
    participante = obter_ou_404(db, Participante, participante_id, "Participante")
    query = (
        db.query(Inscricao)
        .join(Atividade)
        .filter(
            Inscricao.participante_id == participante_id,
            Inscricao.status != StatusInscricao.CANCELADA,
        )
        .order_by(Atividade.inicio.asc())
    )
    if evento_id is not None:
        query = query.filter(Atividade.evento_id == evento_id)
    if inicio_de is not None:
        query = query.filter(Atividade.inicio >= inicio_de.replace(tzinfo=None))
    if inicio_ate is not None:
        query = query.filter(Atividade.fim <= inicio_ate.replace(tzinfo=None))

    itens = [
        ItemProgramacao(
            inscricao_id=insc.id,
            status_inscricao=insc.status,
            presente=insc.presenca is not None,
            atividade=insc.atividade,
        )
        for insc in query.all()
    ]
    return ProgramacaoParticipante(participante=participante, atividades=itens)


@router.get("/consultas/ocupacao-atividades", response_model=list[OcupacaoAtividade])
def consultar_ocupacao_atividades(
    evento_id: int | None = None,
    tipo: TipoAtividade | None = None,
    inicio_de: datetime | None = None,
    inicio_ate: datetime | None = None,
    apenas_com_vagas: bool = False,
    apenas_sem_inscritos: bool = False,
    db: Session = Depends(get_db),
):
    inscritos_expr = func.coalesce(
        func.sum(
            case(
                (Inscricao.id.isnot(None) & (Inscricao.status != StatusInscricao.CANCELADA), 1),
                else_=0,
            )
        ),
        0,
    )
    presencas_expr = func.count(Presenca.id)

    query = (
        db.query(
            Atividade.id,
            Atividade.titulo,
            Atividade.tipo,
            Atividade.status,
            Atividade.inicio,
            Atividade.fim,
            Atividade.capacidade,
            Evento.nome.label("evento_nome"),
            Local.nome.label("local_nome"),
            inscritos_expr.label("inscritos_ativos"),
            presencas_expr.label("total_presencas"),
        )
        .join(Evento, Atividade.evento_id == Evento.id)
        .join(Local, Atividade.local_id == Local.id)
        .outerjoin(Inscricao, Inscricao.atividade_id == Atividade.id)
        .outerjoin(Presenca, Presenca.inscricao_id == Inscricao.id)
    )

    if evento_id is not None:
        query = query.filter(Atividade.evento_id == evento_id)
    if tipo is not None:
        query = query.filter(Atividade.tipo == tipo)
    if inicio_de is not None:
        query = query.filter(Atividade.inicio >= inicio_de.replace(tzinfo=None))
    if inicio_ate is not None:
        query = query.filter(Atividade.fim <= inicio_ate.replace(tzinfo=None))

    query = query.group_by(
        Atividade.id,
        Atividade.titulo,
        Atividade.tipo,
        Atividade.status,
        Atividade.inicio,
        Atividade.fim,
        Atividade.capacidade,
        Evento.nome,
        Local.nome,
    )

    if apenas_sem_inscritos:
        query = query.having(inscritos_expr == 0)
    elif apenas_com_vagas:
        query = query.having(inscritos_expr < Atividade.capacidade)

    linhas = query.order_by(inscritos_expr.desc(), Atividade.inicio.asc()).all()
    return [
        OcupacaoAtividade(
            atividade_id=row.id,
            titulo=row.titulo,
            tipo=row.tipo,
            status=row.status,
            inicio=row.inicio,
            fim=row.fim,
            evento_nome=row.evento_nome,
            local_nome=row.local_nome,
            capacidade=row.capacidade,
            inscritos_ativos=row.inscritos_ativos,
            vagas_disponiveis=max(0, row.capacidade - row.inscritos_ativos),
            total_presencas=row.total_presencas,
            ocupacao_percentual=round((row.inscritos_ativos / row.capacidade) * 100, 1)
            if row.capacidade > 0
            else 0.0,
        )
        for row in linhas
    ]


@router.get("/estatisticas", response_model=EstatisticasGerais)
def obter_estatisticas(evento_id: int | None = None, db: Session = Depends(get_db)):
    if evento_id is not None:
        obter_ou_404(db, Evento, evento_id, "Evento")

    total_eventos = db.query(func.count(Evento.id)).scalar() or 0
    total_locais_ativos = (
        db.query(func.count(Local.id)).filter(Local.ativo.is_(True)).scalar() or 0
    )
    total_participantes_ativos = (
        db.query(func.count(Participante.id)).filter(Participante.ativo.is_(True)).scalar() or 0
    )
    total_palestrantes = db.query(func.count(Palestrante.id)).scalar() or 0

    atv_query = db.query(
        func.count(Atividade.id),
        func.coalesce(func.sum(Atividade.capacidade), 0),
        func.coalesce(func.avg(Atividade.capacidade), 0.0),
    )
    if evento_id is not None:
        atv_query = atv_query.filter(Atividade.evento_id == evento_id)
    total_atividades, capacidade_total, media_capacidade = atv_query.one()

    insc_ativas_query = db.query(func.count(Inscricao.id)).filter(
        Inscricao.status != StatusInscricao.CANCELADA
    )
    if evento_id is not None:
        insc_ativas_query = insc_ativas_query.join(Atividade).filter(
            Atividade.evento_id == evento_id
        )
    total_inscricoes_ativas = insc_ativas_query.scalar() or 0

    pres_query = db.query(func.count(Presenca.id)).join(Inscricao)
    if evento_id is not None:
        pres_query = pres_query.join(Atividade).filter(Atividade.evento_id == evento_id)
    total_presencas = pres_query.scalar() or 0

    por_tipo_query = db.query(Atividade.tipo, func.count(Atividade.id))
    if evento_id is not None:
        por_tipo_query = por_tipo_query.filter(Atividade.evento_id == evento_id)
    atividades_por_tipo = [
        ContagemGrupo(chave=tipo.value, quantidade=qtd)
        for tipo, qtd in por_tipo_query.group_by(Atividade.tipo).all()
    ]

    por_status_query = db.query(Inscricao.status, func.count(Inscricao.id))
    if evento_id is not None:
        por_status_query = por_status_query.join(Atividade).filter(
            Atividade.evento_id == evento_id
        )
    inscricoes_por_status = [
        ContagemGrupo(chave=st.value, quantidade=qtd)
        for st, qtd in por_status_query.group_by(Inscricao.status).all()
    ]

    resumo_ev_query = (
        db.query(
            Evento.id,
            Evento.nome,
            func.count(func.distinct(Atividade.id)).label("total_atividades"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Inscricao.id.isnot(None)
                            & (Inscricao.status != StatusInscricao.CANCELADA),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("total_inscricoes_ativas"),
        )
        .outerjoin(Atividade, Atividade.evento_id == Evento.id)
        .outerjoin(Inscricao, Inscricao.atividade_id == Atividade.id)
    )
    if evento_id is not None:
        resumo_ev_query = resumo_ev_query.filter(Evento.id == evento_id)
    resumo_rows = (
        resumo_ev_query.group_by(Evento.id, Evento.nome)
        .order_by(Evento.data_inicio.asc())
        .all()
    )

    taxa_ocupacao = (
        round((total_inscricoes_ativas / capacidade_total) * 100, 1)
        if capacidade_total
        else 0.0
    )
    taxa_presenca = (
        round((total_presencas / total_inscricoes_ativas) * 100, 1)
        if total_inscricoes_ativas
        else 0.0
    )

    return EstatisticasGerais(
        total_eventos=total_eventos,
        total_locais_ativos=total_locais_ativos,
        total_participantes_ativos=total_participantes_ativos,
        total_palestrantes=total_palestrantes,
        total_atividades=total_atividades or 0,
        total_inscricoes_ativas=int(total_inscricoes_ativas),
        total_presencas=int(total_presencas),
        capacidade_total_atividades=int(capacidade_total or 0),
        media_capacidade_atividade=round(float(media_capacidade or 0.0), 1),
        taxa_ocupacao_percentual=taxa_ocupacao,
        taxa_presenca_percentual=taxa_presenca,
        atividades_por_tipo=atividades_por_tipo,
        inscricoes_por_status=inscricoes_por_status,
        resumo_por_evento=[
            ResumoEventoEstatistica(
                evento_id=row.id,
                evento_nome=row.nome,
                total_atividades=row.total_atividades,
                total_inscricoes_ativas=int(row.total_inscricoes_ativas),
            )
            for row in resumo_rows
        ],
    )
