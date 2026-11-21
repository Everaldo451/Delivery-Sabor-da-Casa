from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field

from app.entities.pedido import FormaPagamento


class PaymentStatus(str, Enum):
    pendente = "pendente"
    aprovado = "aprovado"
    recusado = "recusado"
    cancelado = "cancelado"


class Payment(BaseModel):
    id: int | None = None
    pedido_id: str
    user_id: str
    amount: Decimal
    method: FormaPagamento
    status: PaymentStatus
    simulation_result: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
