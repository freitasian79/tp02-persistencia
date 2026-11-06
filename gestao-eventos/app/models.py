from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

atividade_palestrante = Table(
    'atividade_palestrante', Base.metadata,
    Column('atividade_id', Integer, ForeignKey('atividades.id'), primary_key=True),
    Column('palestrante_id', Integer, ForeignKey('palestrantes.id'), primary_key=True)
)

class Evento(Base):
    __tablename__ = "eventos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    data_inicio = Column(DateTime, nullable=False)
    data_fim = Column(DateTime, nullable=False)
    atividades = relationship("Atividade", back_populates="evento")

class Local(Base):
    __tablename__ = "locais"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    capacidade = Column(Integer, nullable=False)
    ativo = Column(Boolean, default=True)
    atividades = relationship("Atividade", back_populates="local")

class Participante(Base):
    __tablename__ = "participantes"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    ativo = Column(Boolean, default=True)

class Palestrante(Base):
    __tablename__ = "palestrantes"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True, nullable=False)
    especialidade = Column(String, nullable=False)
    atividades = relationship("Atividade", secondary=atividade_palestrante, back_populates="palestrantes")

class Atividade(Base):
    __tablename__ = "atividades"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True, nullable=False)
    descricao = Column(String)
    inicio = Column(DateTime, nullable=False)
    fim = Column(DateTime, nullable=False)
    evento_id = Column(Integer, ForeignKey("eventos.id"))
    local_id = Column(Integer, ForeignKey("locais.id"))
    evento = relationship("Evento", back_populates="atividades")
    local = relationship("Local", back_populates="atividades")
    palestrantes = relationship("Palestrante", secondary=atividade_palestrante, back_populates="atividades")

class Inscricao(Base):
    __tablename__ = "inscricoes"
    
    id = Column(Integer, primary_key=True, index=True)
    participante_id = Column(Integer, ForeignKey("participantes.id"), nullable=False)
    atividade_id = Column(Integer, ForeignKey("atividades.id"), nullable=False)
    status = Column(String, default="confirmada") # ex: confirmada, cancelada
    
    participante = relationship("Participante", backref="inscricoes")
    atividade = relationship("Atividade", backref="inscricoes")