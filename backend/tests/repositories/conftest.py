import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config


@pytest.fixture(scope="session", autouse=True)
def migrar_banco_de_testes() -> None:
    """Prepara o PostgreSQL de teste com o schema da aplicação."""
    if os.getenv("RUN_REPOSITORY_MIGRATIONS") != "1":
        return
    backend = Path(__file__).resolve().parents[2]
    config = Config(str(backend / "alembic.ini"))
    command.upgrade(config, "head")
