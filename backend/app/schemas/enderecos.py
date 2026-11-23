from pydantic import BaseModel, Field


class SugestaoEnderecoOut(BaseModel):
    descricao: str
    rua: str
    numero: str | None = None
    bairro: str
    cidade: str
    estado: str
    cep: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
