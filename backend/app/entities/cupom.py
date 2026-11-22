from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class TipoDescontoCupom(str, Enum):
    percentual = "percentual"
    valor_fixo = "valor_fixo"


class Cupom(BaseModel):
    id: int | None = None
    codigo: str = Field(min_length=3, max_length=30)
    descricao: str = Field(min_length=1, max_length=250)
    tipo: TipoDescontoCupom
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    subtotal_minimo: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)
    desconto_maximo: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    limite_usos: int | None = Field(default=None, gt=0)
    limite_por_usuario: int | None = Field(default=1, gt=0)
    somente_novos_clientes: bool = False
    valido_de: date | None = None
    valido_ate: date | None = None
    ativo: bool = True
