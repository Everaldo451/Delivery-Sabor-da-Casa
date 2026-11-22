from decimal import Decimal

from pydantic import BaseModel, Field


class Categoria(BaseModel):
    id: int
    nome: str = Field(min_length=1, max_length=80)


class ImagemPrato(BaseModel):
    imagem: bytes | None = None
    content_type: str = Field(max_length=50)


class Prato(BaseModel):
    id: str | None = None
    nome: str = Field(min_length=1, max_length=120)
    descricao: str = Field(min_length=1, max_length=2000)
    preco: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    categoria: str = Field(min_length=1, max_length=80)
    imagem: ImagemPrato | None = None
    disponivel: bool = True
