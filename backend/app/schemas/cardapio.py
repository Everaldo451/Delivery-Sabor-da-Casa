from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class CategoriaOut(BaseModel):
    id: int
    nome: str


class CategoriaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=80)

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, nome: str) -> str:
        nome = nome.strip()
        if not nome:
            raise ValueError("O nome da categoria nao pode ficar vazio")
        return nome


class CategoriaAtualizar(CategoriaCreate):
    pass


class PratoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    descricao: str = Field(min_length=1, max_length=2000)
    preco: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    categoria: str = Field(min_length=1, max_length=80)
    disponivel: bool = True


class PratoAtualizar(PratoCreate):
    pass


class ImagemPratoOut(BaseModel):
    url: str
    content_type: str


class PratoOut(BaseModel):
    id: str
    nome: str
    descricao: str
    preco: Decimal
    categoria: str
    imagem: ImagemPratoOut | None = None
    disponivel: bool
