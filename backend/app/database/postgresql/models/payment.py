from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Numeric
from sqlmodel import Field, SQLModel

from app.entities.payment import PaymentStatus
from app.entities.pedido import FormaPagamento


class PaymentModel(SQLModel, table=True):
    __tablename__ = "payments"

    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: str = Field(index=True)
    user_id: str = Field(index=True)
    amount: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    method: FormaPagamento = Field(index=True)
    status: PaymentStatus = Field(default=PaymentStatus.pendente, index=True)
    simulation_result: Optional[str] = Field(default=None, max_length=20)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
