from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

from starlette.websockets import WebSocketDisconnect

from app.entities.pedido import EnderecoEntrega, FormaPagamento, StatusPedido
from app.entities.usuario import Usuario
from app.schemas.pedidos import ItemPedidoOut, PedidoOut
from app.services.pedido_eventos_service import PedidoEventosService


def pedido_saida() -> PedidoOut:
    agora = datetime.now(timezone.utc)
    return PedidoOut(
        id="pedido-1",
        user_id="cliente-1",
        itens=[
            ItemPedidoOut(
                prato_id="prato-1",
                nome="Prato",
                preco_unitario=20,
                quantidade=1,
            )
        ],
        subtotal=20,
        desconto=0,
        taxa_entrega=5,
        total=25,
        endereco_entrega=EnderecoEntrega(
            rua="Rua Teste", numero="10", bairro="Centro", cep="01310930"
        ),
        forma_pagamento=FormaPagamento.pix,
        status=StatusPedido.aguardando_pagamento,
        criado_em=agora,
        atualizado_em=agora,
    )


def websocket_mock():
    websocket = Mock()
    websocket.send_json = AsyncMock()
    return websocket


async def test_publica_pedido_novo_para_todas_as_conexoes():
    service = PedidoEventosService(Mock())
    conexoes = [websocket_mock(), websocket_mock()]
    service._conexoes.update(conexoes)
    pedido = pedido_saida()

    await service.pedido_criado(pedido)

    mensagem = {
        "evento": "pedido_criado",
        "pedido": pedido.model_dump(mode="json"),
    }
    for websocket in conexoes:
        websocket.send_json.assert_awaited_once_with(mensagem)


async def test_remove_conexao_que_falha_ao_receber_evento(caplog):
    service = PedidoEventosService(Mock())
    websocket = websocket_mock()
    websocket.send_json.side_effect = RuntimeError("conexao fechada")
    service._conexoes.add(websocket)

    await service.pedido_criado(pedido_saida())

    assert websocket not in service._conexoes
    assert "Falha ao publicar evento de pedido" in caplog.text


async def test_conexao_administrativa_e_removida_ao_desconectar():
    auth_service = Mock()
    auth_service.usuario_por_token = AsyncMock(
        return_value=Usuario(
            id="admin-1", email="admin@example.com", senha_hash="", is_admin=True
        )
    )
    service = PedidoEventosService(auth_service)
    websocket = Mock()
    websocket.accept = AsyncMock()
    websocket.receive_text = AsyncMock(
        side_effect=WebSocketDisconnect(code=1000)
    )
    websocket.close = AsyncMock()

    await service.acompanhar(websocket, "access-token")

    auth_service.usuario_por_token.assert_awaited_once_with("access-token")
    websocket.accept.assert_awaited_once_with()
    assert websocket not in service._conexoes


async def test_usuario_comum_nao_abre_conexao_de_eventos():
    auth_service = Mock()
    auth_service.usuario_por_token = AsyncMock(
        return_value=Usuario(
            id="cliente-1", email="cliente@example.com", senha_hash="", is_admin=False
        )
    )
    service = PedidoEventosService(auth_service)
    websocket = Mock()
    websocket.close = AsyncMock()
    websocket.accept = AsyncMock()

    await service.acompanhar(websocket, "access-token")

    websocket.close.assert_awaited_once_with(code=4403)
    websocket.accept.assert_not_awaited()
