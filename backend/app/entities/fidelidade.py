from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class TransacaoFidelidade(BaseModel):
    id: int
    user_id: str
    pedido_id: str | None = None
    pontos: int
    tipo: str
    criado_em: datetime


class SaldoFidelidade(BaseModel):
    user_id: str
    pontos: int
    valor_resgate_reais: Decimal
