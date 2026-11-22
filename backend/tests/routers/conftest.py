from collections.abc import Generator
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.entities.usuario import Usuario
from app.routers import include_routers
from app.routers import (
    auth,
    cardapio,
    carrinho,
    cupons,
    favoritos,
    fidelidade,
    payments,
    pedidos,
)


@pytest.fixture
def usuario_teste() -> Usuario:
    return Usuario(
        id="usuario-teste",
        nome="Cliente Teste",
        email="cliente@example.com",
        senha_hash="hash-nao-usado",
        is_admin=True,
    )


@pytest.fixture
def app(usuario_teste: Usuario) -> FastAPI:
    application = FastAPI()
    include_routers(application)

    async def usuario_logado() -> Usuario:
        return usuario_teste

    async def usuario_admin() -> Usuario:
        return usuario_teste

    for module in (cardapio, carrinho, cupons, favoritos, fidelidade, payments, pedidos):
        application.dependency_overrides[module.auth_service.usuario_logado] = usuario_logado
        application.dependency_overrides[module.auth_service.usuario_admin] = usuario_admin
    application.dependency_overrides[auth.auth_service.obter_token] = lambda: "token-teste"
    return application


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def service_mock() -> Mock:
    return Mock()
