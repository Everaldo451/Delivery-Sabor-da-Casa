import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from unittest.mock import Mock


@pytest.fixture(scope="session", autouse=True)
def migrar_banco_de_testes() -> None:
    """Prepara o PostgreSQL de teste com o schema da aplicação."""
    if os.getenv("RUN_REPOSITORY_MIGRATIONS") != "1":
        return
    backend = Path(__file__).resolve().parents[2]
    config = Config(str(backend / "alembic.ini"))
    command.upgrade(config, "head")


@pytest.fixture
def mock_postgres_session() -> Mock:
    session = Mock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    return session


@pytest.fixture
def sqlite_postgres(monkeypatch):
    """Database SQLite real para testar queries SQLModel sem serviços externos."""
    from sqlmodel import SQLModel, Session, create_engine

    import app.database.postgresql  # Registra todos os modelos no metadata.
    from app.repositories import (
        cardapio_repository,
        cupom_repository,
        favorito_repository,
        fidelidade_repository,
        payment_repository,
        user_repository,
    )

    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    def criar_sessao():
        return Session(engine)

    for module in (
        cardapio_repository,
        cupom_repository,
        favorito_repository,
        fidelidade_repository,
        payment_repository,
        user_repository,
    ):
        monkeypatch.setattr(module, "create_session", criar_sessao)

    yield engine
    engine.dispose()
