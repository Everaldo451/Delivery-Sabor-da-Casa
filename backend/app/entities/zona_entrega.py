from pydantic import BaseModel, Field

from app.types.geografia import AreaGeografica


class ZonaEntrega(BaseModel):
    nome: str = Field(min_length=1)
    area: AreaGeografica
    valor: float = Field(ge=0)
