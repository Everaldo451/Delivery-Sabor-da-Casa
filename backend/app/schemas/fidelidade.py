from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SaldoFidelidadeOut(BaseModel):
    user_id: str
    pontos: int
    valor_resgate_reais: Decimal
    pontos_por_real: int = 100


class TransacaoFidelidadeOut(BaseModel):
    id: int
    pedido_id: str | None
    pontos: int
    tipo: str
    criado_em: datetime


