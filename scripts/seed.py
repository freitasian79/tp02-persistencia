from datetime import date, datetime
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.database import SessionLocal
from app.models import (
    Atividade,
    Evento,
    Inscricao,
    Local,
    Palestrante,
    Participante,
    Presenca,
)
from app.models.enums import (
    StatusAtividade,
    StatusEvento,
    StatusInscricao,
    TipoAtividade,
    TipoEvento,
    TipoLocal,
)


def povoar_banco() -> None:
    db = SessionLocal()
    try:
        if db.query(Evento).first() is not None:
            print("Banco já possui dados iniciais. Povoamento ignorado.")
            return

        locais = [
            Local(
                nome="Auditório Central",
                tipo=TipoLocal.AUDITORIO,
                capacidade=120,
                localizacao="Bloco Administrativo, térreo",
                recursos="Projetor 4K, sistema de som, transmissão",
            ),
            Local(
                nome="Laboratório de Redes",
                tipo=TipoLocal.LABORATORIO,
                capacidade=25,
                localizacao="Bloco 2, sala 204",
                recursos="25 estações Linux, quadro branco",
            ),
            Local(
                nome="Sala de Seminários 1",
                tipo=TipoLocal.SALA,
                capacidade=4,
                localizacao="Bloco 1, sala 105",
                recursos="TV 65 polegadas, ar-condicionado",
            ),
            Local(
                nome="Anfiteatro Externo",
                tipo=TipoLocal.OUTRO,
                capacidade=60,
                localizacao="Área de convivência",
                recursos="Cobertura e caixa de som",
                ativo=False,
            ),
        ]
        db.add_all(locais)
        db.flush()

        eventos = [
            Evento(
                nome="Semana de Tecnologia da UFC Quixadá 2026",
                descricao="Palestras, minicursos e oficinas voltados à engenharia de software e dados.",
                tipo=TipoEvento.CONGRESSO,
                data_inicio=date(2026, 11, 10),
                data_fim=date(2026, 11, 13),
                organizador="Coordenação de Computação",
                status=StatusEvento.ATIVO,
            ),
            Evento(
                nome="Simpósio Regional de Banco de Dados",
                descricao="Encontros técnicos sobre modelagem relacional, SQL e NoSQL.",
                tipo=TipoEvento.SIMPOSIO,
                data_inicio=date(2026, 12, 2),
                data_fim=date(2026, 12, 3),
                organizador="Núcleo de Persistência",
                status=StatusEvento.ATIVO,
            ),
            Evento(
                nome="Workshop de Arquitetura Web",
                descricao="Edição anterior já finalizada.",
                tipo=TipoEvento.WORKSHOP,
                data_inicio=date(2026, 8, 15),
                data_fim=date(2026, 8, 16),
                organizador="PET-SI",
                status=StatusEvento.ENCERRADO,
            ),
        ]
        db.add_all(eventos)
        db.flush()

        palestrantes = [
            Palestrante(
                nome="Profa. Camila Nogueira",
                email="camila.nogueira@ufc.br",
                area_atuacao="Engenharia de Dados",
                mini_bio="Pesquisadora em bancos relacionais e pipelines analíticos.",
            ),
            Palestrante(
                nome="Prof. Ricardo Mendes",
                email="ricardo.mendes@ufc.br",
                area_atuacao="Desenvolvimento Backend",
                mini_bio="Atua com APIs REST em Python, FastAPI e microsserviços.",
            ),
            Palestrante(
                nome="Fernanda Lima",
                email="fernanda.lima@techce.com.br",
                area_atuacao="Arquitetura em Nuvem",
                mini_bio="Arquiteta de soluções distribuídas e observabilidade.",
            ),
            Palestrante(
                nome="Lucas Teixeira",
                email="lucas.teixeira@dados.org",
                area_atuacao="Segurança de Aplicações",
                mini_bio="Especialista em hardening de APIs e controle de acesso.",
            ),
        ]
        db.add_all(palestrantes)
        db.flush()

        atividades = [
            Atividade(
                evento_id=eventos[0].id,
                local_id=locais[0].id,
                titulo="Abertura: Persistência Moderna com Python",
                descricao="Visão geral sobre ORM, migrações e boas práticas.",
                tipo=TipoAtividade.PALESTRA,
                inicio=datetime(2026, 11, 10, 9, 0),
                fim=datetime(2026, 11, 10, 11, 0),
                capacidade=80,
                carga_horaria=2,
                palestrantes=[palestrantes[0], palestrantes[1]],
            ),
            Atividade(
                evento_id=eventos[0].id,
                local_id=locais[1].id,
                titulo="Minicurso de FastAPI e SQLAlchemy",
                descricao="Construção prática de endpoints REST com PostgreSQL.",
                tipo=TipoAtividade.MINICURSO,
                inicio=datetime(2026, 11, 10, 14, 0),
                fim=datetime(2026, 11, 10, 18, 0),
                capacidade=20,
                carga_horaria=4,
                palestrantes=[palestrantes[1]],
            ),
            Atividade(
                evento_id=eventos[0].id,
                local_id=locais[2].id,
                titulo="Oficina Intensiva de Tuning SQL",
                descricao="Turma reduzida para análise de planos de execução.",
                tipo=TipoAtividade.OFICINA,
                inicio=datetime(2026, 11, 11, 9, 0),
                fim=datetime(2026, 11, 11, 12, 0),
                capacidade=3,
                carga_horaria=3,
                palestrantes=[palestrantes[0]],
            ),
            Atividade(
                evento_id=eventos[0].id,
                local_id=locais[0].id,
                titulo="Mesa-Redonda: Mercado de Software no Interior",
                descricao="Debate com egressos e professores.",
                tipo=TipoAtividade.MESA_REDONDA,
                inicio=datetime(2026, 11, 12, 16, 0),
                fim=datetime(2026, 11, 12, 18, 0),
                capacidade=100,
                carga_horaria=2,
                palestrantes=[palestrantes[1], palestrantes[2], palestrantes[3]],
            ),
            Atividade(
                evento_id=eventos[1].id,
                local_id=locais[0].id,
                titulo="Modelagem Relacional e Integridade",
                descricao="Boas práticas de restrições e normalização.",
                tipo=TipoAtividade.PALESTRA,
                inicio=datetime(2026, 12, 2, 10, 0),
                fim=datetime(2026, 12, 2, 12, 0),
                capacidade=50,
                carga_horaria=2,
                palestrantes=[palestrantes[0]],
            ),
            Atividade(
                evento_id=eventos[1].id,
                local_id=locais[1].id,
                titulo="Oficina de Migrações com Alembic",
                descricao="Evolução de esquema sem perda de dados.",
                tipo=TipoAtividade.OFICINA,
                inicio=datetime(2026, 12, 3, 14, 0),
                fim=datetime(2026, 12, 3, 16, 0),
                capacidade=20,
                carga_horaria=2,
                status=StatusAtividade.AGENDADA,
                palestrantes=[palestrantes[2]],
            ),
        ]
        db.add_all(atividades)
        db.flush()

        dados_participantes = [
            ("Ana Beatriz Souza", "ana.beatriz@alu.ufc.br", "10120230301", "88999000101", "UFC Quixadá", True),
            ("Bruno Henrique Alves", "bruno.alves@alu.ufc.br", "10120230302", "88999000102", "UFC Quixadá", True),
            ("Carla Vitória Lima", "carla.lima@alu.ufc.br", "10120230303", "88999000103", "IFCE Quixadá", True),
            ("Daniel Rocha", "daniel.rocha@alu.ufc.br", "10120230304", "88999000104", "UFC Quixadá", True),
            ("Eduarda Monteiro", "eduarda.monteiro@alu.ufc.br", "10120230305", "88999000105", "UECE", True),
            ("Felipe Vasconcelos", "felipe.vasc@alu.ufc.br", "10120230306", "88999000106", "UFC Quixadá", True),
            ("Gabriela Martins", "gabriela.m@alu.ufc.br", "10120230307", "88999000107", "IFCE Quixadá", True),
            ("Henrique Costa", "henrique.costa@alu.ufc.br", "10120230308", "88999000108", "UFC Fortaleza", True),
            ("Isabela Ferreira", "isabela.f@alu.ufc.br", "10120230309", "88999000109", "UFC Quixadá", True),
            ("João Pedro Nobre", "joao.nobre@alu.ufc.br", "10120230310", "88999000110", "UFC Quixadá", True),
            ("Larissa Cavalcante", "larissa.c@alu.ufc.br", "10120230311", "88999000111", "UNICATÓLICA", True),
            ("Mateus Barros", "mateus.barros@alu.ufc.br", "10120230312", "88999000112", "UFC Quixadá", False),
        ]
        participantes = [
            Participante(
                nome=nome,
                email=email,
                cpf=cpf,
                telefone=tel,
                instituicao=inst,
                ativo=ativo,
            )
            for nome, email, cpf, tel, inst, ativo in dados_participantes
        ]
        db.add_all(participantes)
        db.flush()

        # Inscrições (atividade[2] fica lotada com 3/3 para demonstrar F17; atividade[5] fica sem inscritos para F11)
        inscricoes = [
            Inscricao(participante_id=participantes[0].id, atividade_id=atividades[0].id, status=StatusInscricao.CONFIRMADA),
            Inscricao(participante_id=participantes[1].id, atividade_id=atividades[0].id, status=StatusInscricao.CONFIRMADA),
            Inscricao(participante_id=participantes[2].id, atividade_id=atividades[0].id, status=StatusInscricao.CONFIRMADA),
            Inscricao(participante_id=participantes[3].id, atividade_id=atividades[0].id, status=StatusInscricao.PENDENTE),
            Inscricao(participante_id=participantes[0].id, atividade_id=atividades[1].id, status=StatusInscricao.CONFIRMADA),
            Inscricao(participante_id=participantes[1].id, atividade_id=atividades[1].id, status=StatusInscricao.CONFIRMADA),
            Inscricao(participante_id=participantes[4].id, atividade_id=atividades[1].id, status=StatusInscricao.CANCELADA, observacao="Desistência por conflito pessoal"),
            Inscricao(participante_id=participantes[0].id, atividade_id=atividades[2].id, status=StatusInscricao.CONFIRMADA),
            Inscricao(participante_id=participantes[5].id, atividade_id=atividades[2].id, status=StatusInscricao.CONFIRMADA),
            Inscricao(participante_id=participantes[6].id, atividade_id=atividades[2].id, status=StatusInscricao.CONFIRMADA),
            Inscricao(participante_id=participantes[7].id, atividade_id=atividades[3].id, status=StatusInscricao.CONFIRMADA),
            Inscricao(participante_id=participantes[8].id, atividade_id=atividades[3].id, status=StatusInscricao.CONFIRMADA),
            Inscricao(participante_id=participantes[9].id, atividade_id=atividades[4].id, status=StatusInscricao.CONFIRMADA),
            Inscricao(participante_id=participantes[10].id, atividade_id=atividades[4].id, status=StatusInscricao.CONFIRMADA),
        ]
        db.add_all(inscricoes)
        db.flush()

        presencas = [
            Presenca(inscricao_id=inscricoes[0].id, metodo="qrcode"),
            Presenca(inscricao_id=inscricoes[1].id, metodo="manual"),
            Presenca(inscricao_id=inscricoes[4].id, metodo="qrcode"),
            Presenca(inscricao_id=inscricoes[7].id, metodo="manual"),
            Presenca(inscricao_id=inscricoes[10].id, metodo="qrcode"),
        ]
        db.add_all(presencas)

        db.commit()
        print("Banco povoado com sucesso.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    povoar_banco()
