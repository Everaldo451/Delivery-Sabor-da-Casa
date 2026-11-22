from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlmodel import Field, SQLModel


class CupomUsoModel(SQLModel, table=True):
    __tablename__ = "usos_cupom"
    __table_args__ = (
        UniqueConstraint("cupom_id", "pedido_id", name="uq_usos_cupom_pedido"),
    )

    id: int | None = Field(default=None, primary_key=True)
    cupom_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("cupons.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
    user_id: str = Field(
        sa_column=Column(
            String,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    pedido_id: str = Field(max_length=100, index=True)
    usado_em: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
