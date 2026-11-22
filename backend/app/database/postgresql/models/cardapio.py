from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Column, ForeignKey, LargeBinary, Numeric, Text
from sqlmodel import Field, Relationship, SQLModel


class CategoriaModel(SQLModel, table=True):
    __tablename__ = "categorias"

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(unique=True, index=True, max_length=80)
    pratos: list["PratoModel"] = Relationship(back_populates="categoria")


class PratoModel(SQLModel, table=True):
    __tablename__ = "pratos"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    nome: str = Field(max_length=120, index=True)
    descricao: str = Field(sa_column=Column(Text, nullable=False))
    preco: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    categoria_id: int = Field(
        sa_column=Column(
            ForeignKey("categorias.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
    imagem: bytes | None = Field(
        default=None,
        sa_column=Column("imagem_dados", LargeBinary, nullable=True),
    )
    imagem_content_type: str | None = Field(default=None, max_length=50)
    disponivel: bool = Field(default=True, index=True)
    categoria: CategoriaModel = Relationship(back_populates="pratos")
