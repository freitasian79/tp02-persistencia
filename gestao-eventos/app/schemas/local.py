from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TipoLocal


class LocalBase(BaseModel):
    nome: str = Field(min_length=2, max_length=120, examples=["Laboratório 3"])
    tipo: TipoLocal
    capacidade: int = Field(gt=0, le=10000, examples=[20])
    localizacao: str | None = Field(default=None, max_length=200, examples=["Bloco 1, térreo"])
    recursos: str | None = Field(default=None, examples=["20 computadores, projetor"])


class LocalCreate(LocalBase):
    pass


class LocalUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    tipo: TipoLocal | None = None
    capacidade: int | None = Field(default=None, gt=0, le=10000)
    localizacao: str | None = Field(default=None, max_length=200)
    recursos: str | None = None
    ativo: bool | None = None


class LocalRead(LocalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool