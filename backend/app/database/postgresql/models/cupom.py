from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Column, Date, Integer, Numeric, String, Text
from sqlmodel import Field, SQLModel


class CupomModel(SQLModel, table=True):
    __tablename__ = "cupons"

    id: int | None = Field(default=None, primary_key=True)
    codigo: str = Field(sa_column=Column(String(30), nullable=False, unique=True, index=True))
    descricao: str = Field(sa_column=Column(Text, nullable=False))
    tipo: str = Field(sa_column=Column(String(20), nullable=False))
    valor: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    subtotal_minimo: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0"),
    )
    desconto_maximo: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(10, 2), nullable=True),
    )
    limite_usos: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    limite_por_usuario: int | None = Field(
        default=1,
        sa_column=Column(Integer, nullable=True, server_default="1"),
    )
    somente_novos_clientes: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default="false"),
    )
    valido_de: date | None = Field(default=None, sa_column=Column(Date, nullable=True))
    valido_ate: date | None = Field(default=None, sa_column=Column(Date, nullable=True))
    ativo: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, server_default="true"))
