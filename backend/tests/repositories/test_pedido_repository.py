from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

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


async def test_listar_todos_retorna_pagina_e_total(monkeypatch):
    class Cursor:
        def __init__(self):
            self.operacoes = []

        def sort(self, campo, ordem):
            self.operacoes.append(("sort", campo, ordem))
            return self

        def skip(self, quantidade):
            self.operacoes.append(("skip", quantidade))
            return self

        def limit(self, quantidade):
            self.operacoes.append(("limit", quantidade))
            return self

        def __aiter__(self):
            async def iterar():
                yield {"pedido": "a"}
                yield {"pedido": "b"}

            return iterar()

    cursor = Cursor()
    collection = Mock()
    collection.count_documents = AsyncMock(return_value=25)
    collection.find.return_value = cursor
    monkeypatch.setattr(
        "app.repositories.pedido_repository.get_mongo_db",
        lambda: {"pedidos": collection},
    )
    repository = PedidosRepository()
    repository._para_entidade = Mock(side_effect=["pedido-a", "pedido-b"])

    pedidos, total = await repository.listar_todos(pagina=2, limite=10)

    assert pedidos == ["pedido-a", "pedido-b"]
    assert total == 25
    collection.count_documents.assert_awaited_once_with({})
    assert cursor.operacoes == [
        ("sort", "criado_em", -1),
        ("skip", 10),
        ("limit", 10),
    ]
