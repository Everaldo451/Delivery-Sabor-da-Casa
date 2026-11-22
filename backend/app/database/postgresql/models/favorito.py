from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlmodel import Field, SQLModel


class FavoritoModel(SQLModel, table=True):
    __tablename__ = "favoritos"

    user_id: str = Field(
        sa_column=Column(
            String,
            ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    prato_id: str = Field(
        sa_column=Column(
            String,
            ForeignKey("pratos.id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
