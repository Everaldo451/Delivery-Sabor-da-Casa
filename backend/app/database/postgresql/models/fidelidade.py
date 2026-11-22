from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlmodel import Field, SQLModel


class TransacaoFidelidadeModel(SQLModel, table=True):
    __tablename__ = "transacoes_fidelidade"
    __table_args__ = (
        UniqueConstraint(
            "pedido_id",
            "tipo",
            name="uq_transacoes_fidelidade_pedido_tipo",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(
        sa_column=Column(
            String,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    pedido_id: str | None = Field(default=None, max_length=100, index=True)
    pontos: int = Field(sa_column=Column(Integer, nullable=False))
    tipo: str = Field(max_length=30, index=True)
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
