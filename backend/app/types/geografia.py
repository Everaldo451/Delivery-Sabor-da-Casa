from pydantic import BaseModel, Field, model_validator


class CoordenadaGeografica(BaseModel):
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)


class AnelGeografico(BaseModel):
    pontos: list[CoordenadaGeografica] = Field(min_length=4)

    @model_validator(mode="after")
    def validar_fechamento(self) -> "AnelGeografico":
        if self.pontos[0] != self.pontos[-1]:
            raise ValueError("O anel geografico precisa ser fechado")
        return self


class PoligonoGeografico(BaseModel):
    aneis: list[AnelGeografico] = Field(min_length=1)


class AreaGeografica(BaseModel):
    poligonos: list[PoligonoGeografico] = Field(min_length=1)
