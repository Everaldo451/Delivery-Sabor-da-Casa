from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.entities.payment import PaymentStatus
from app.entities.pedido import FormaPagamento


class CheckoutCreate(BaseModel):
    pedido_id: str
    method: FormaPagamento
    simulation_result: PaymentStatus | None = Field(
        default=PaymentStatus.aprovado,
        description="Resultado opcional da simulacao: aprovado ou recusado",
    )


class PaymentOut(BaseModel):
    id: int
    pedido_id: str
    user_id: str
    amount: Decimal
    method: FormaPagamento
    status: PaymentStatus
    simulation_result: str | None = None
    created_at: datetime
    updated_at: datetime
