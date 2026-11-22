import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlmodel import Session, create_engine

from app.database.postgresql.models.cardapio import (
    CategoriaModel as _CategoriaModel,
    PratoModel as _PratoModel,
)
from app.database.postgresql.models.payment import PaymentModel as _PaymentModel
from app.database.postgresql.models.user import UserModel as _UserModel

__all__ = ["DATABASE_URL", "create_session", "engine", "get_session"]

load_dotenv()

DATABASE_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/sabordacasa",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def create_session() -> Session:
    return Session(engine)


def get_session() -> Generator[Session, None, None]:
    with create_session() as session:
        yield session
