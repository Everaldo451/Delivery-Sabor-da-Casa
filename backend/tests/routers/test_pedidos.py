from unittest.mock import AsyncMock, Mock

from fastapi import HTTPException
from app.routers import pedidos
from app.schemas.pedidos import PedidosPaginaOut


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


def test_admin_lista_pedidos_paginados(client):
    service = AsyncMock()
    service.listar_admin.return_value = PedidosPaginaOut(
        pedidos=[], pagina=2, limite=10, total=23, total_paginas=3
    )
    client.app.dependency_overrides[pedidos.get_pedido_service] = lambda: service

    response = client.get("/pedidos/admin?pagina=2&limite=10")

    assert response.status_code == 200
    assert response.json() == {
        "pedidos": [],
        "pagina": 2,
        "limite": 10,
        "total": 23,
        "total_paginas": 3,
    }
    service.listar_admin.assert_awaited_once_with(2, 10)


def test_usuario_comum_nao_pode_listar_pedidos_admin(client):
    async def rejeitar_usuario_comum():
        raise HTTPException(status_code=403, detail="Usuario sem permissao")

    client.app.dependency_overrides[pedidos.auth_service.usuario_admin] = (
        rejeitar_usuario_comum
    )
    service = Mock()
    service.listar_admin = AsyncMock(
        return_value=PedidosPaginaOut(
            pedidos=[], pagina=1, limite=20, total=0, total_paginas=0
        )
    )
    client.app.dependency_overrides[pedidos.get_pedido_service] = lambda: service

    response = client.get("/pedidos/admin")

    assert response.status_code == 403


def test_listagem_admin_valida_limites_de_paginacao(client):
    assert client.get("/pedidos/admin?pagina=0").status_code == 422
    assert client.get("/pedidos/admin?limite=51").status_code == 422


def test_websocket_de_pedidos_delega_conexao_ao_service(client):
    eventos = Mock()

    async def conectar(websocket, token):
        await websocket.accept()
        await websocket.send_json({"evento": "conectado"})

    eventos.acompanhar = AsyncMock(side_effect=conectar)
    client.app.dependency_overrides[pedidos.get_pedido_eventos_service] = lambda: eventos

    with client.websocket_connect(
        "/pedidos/realtime-orders?token=token-teste"
    ) as websocket:
        assert websocket.receive_json() == {"evento": "conectado"}

    eventos.acompanhar.assert_awaited_once()
    assert eventos.acompanhar.call_args.args[1] == "token-teste"
