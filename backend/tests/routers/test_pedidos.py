from unittest.mock import AsyncMock

from app.routers import pedidos


def test_historico_pedido_retorna_lista(client):
    service = AsyncMock()
    service.historico.return_value = []
    client.app.dependency_overrides[pedidos.get_pedido_service] = lambda: service

    response = client.get("/pedidos?pagina=2&limite=10")

    assert response.status_code == 200
    assert response.json() == []
    service.historico.assert_awaited_once()
    assert service.historico.call_args.args[:2] == (2, 10)


def test_paginacao_invalida_retorna_422(client):
    assert client.get("/pedidos?pagina=0").status_code == 422
