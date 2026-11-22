from unittest.mock import AsyncMock

from app.routers import carrinho
from app.schemas.carrinho import CarrinhoOut


def test_adicionar_item_do_carrinho(client):
    service = AsyncMock()
    service.adicionar.return_value = CarrinhoOut(
        user_id="usuario-teste", itens=[{"prato_id": "p-1", "quantidade": 2}]
    )
    client.app.dependency_overrides[carrinho.get_carrinho_service] = lambda: service

    response = client.post("/carrinho/itens", json={"prato_id": "p-1", "quantidade": 2})

    assert response.status_code == 200
    assert response.json()["itens"][0]["quantidade"] == 2
    service.adicionar.assert_awaited_once()


def test_limpar_carrinho_retorna_204(client):
    service = AsyncMock()
    client.app.dependency_overrides[carrinho.get_carrinho_service] = lambda: service

    response = client.delete("/carrinho")

    assert response.status_code == 204
    service.limpar.assert_awaited_once()


def test_item_invalido_retorna_422(client):
    assert client.post("/carrinho/itens", json={"prato_id": "p-1", "quantidade": 0}).status_code == 422
