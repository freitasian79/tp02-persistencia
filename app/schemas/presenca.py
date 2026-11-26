from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PresencaCreate(BaseModel):
    inscricao_id: int = Field(gt=0)
    metodo: Literal["manual", "qrcode"] = "manual"


class PresencaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inscricao_id: int
    registrada_em: datetime
    metodo: str