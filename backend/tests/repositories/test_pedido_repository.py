from datetime import datetime, timezone

from app.entities.pedido import EnderecoEntrega, FormaPagamento, ItemPedido, Pedido, StatusPedido
from app.repositories.pedido_repository import PedidosRepository


def test_documento_mongo_preserva_snapshot_do_pedido():
    now = datetime.now(timezone.utc)
    pedido = Pedido(
        id=None, user_id="u-1",
        itens=[ItemPedido(prato_id="p-1", nome="Prato", preco_unitario=10, quantidade=2)],
        subtotal=20, desconto=0, taxa_entrega=3, total=23,
        endereco_entrega=EnderecoEntrega(rua="Rua", numero="1", bairro="Centro"),
        forma_pagamento=FormaPagamento.dinheiro, status=StatusPedido.recebido,
        criado_em=now, atualizado_em=now,
    )

    doc = PedidosRepository()._para_documento(pedido)

    assert "id" not in doc
    assert doc["user_id"] == "u-1"
    assert doc["itens"][0]["preco_unitario"] == 10
    assert doc["forma_pagamento"] == "dinheiro"
    assert "localizacao" not in doc["endereco_entrega"]
