from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PalestranteBase(BaseModel):
    nome: str = Field(min_length=3, max_length=150)
    email: EmailStr
    area_atuacao: str | None = Field(default=None, max_length=120)
    mini_bio: str | None = None


class PalestranteCreate(PalestranteBase):
    pass


class PalestranteUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=3, max_length=150)
    email: EmailStr | None = None
    area_atuacao: str | None = Field(default=None, max_length=120)
    mini_bio: str | None = None


class PalestranteRead(PalestranteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int