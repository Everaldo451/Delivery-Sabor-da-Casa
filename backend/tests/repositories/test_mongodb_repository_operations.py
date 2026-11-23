from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

from bson import ObjectId

from app.entities.pedido import EnderecoEntrega, FormaPagamento, ItemPedido, Pedido, StatusPedido
from app.entities.zona_entrega import ZonaEntrega
from app.repositories.pedido_repository import PedidosRepository
from app.repositories.zona_entrega_repository import ZonaEntregaRepository
from app.types.geografia import (
    AnelGeografico,
    AreaGeografica,
    CoordenadaGeografica,
    PoligonoGeografico,
)


class AsyncCursor:
    def __init__(self, documents):
        self.documents = documents
        self.operations = []

    def sort(self, field, direction):
        self.operations.append(("sort", field, direction))
        return self

    def skip(self, amount):
        self.operations.append(("skip", amount))
        return self

    def limit(self, amount):
        self.operations.append(("limit", amount))
        return self

    def __aiter__(self):
        async def iterate():
            for document in self.documents:
                yield document
        return iterate()


def pedido_fixture(pedido_id: ObjectId | None = None, with_location=False):
    now = datetime.now(timezone.utc)
    location = CoordenadaGeografica(longitude=-46.63, latitude=-23.55) if with_location else None
    pedido = Pedido(
        id=str(pedido_id or ObjectId()),
        user_id="user-1",
        itens=[ItemPedido(prato_id="dish-1", nome="Prato", preco_unitario=12.5, quantidade=2)],
        subtotal=25,
        desconto=0,
        taxa_entrega=3,
        total=28,
        endereco_entrega=EnderecoEntrega(rua="Rua A", numero="1", bairro="Centro", localizacao=location),
        forma_pagamento=FormaPagamento.pix,
        status=StatusPedido.recebido,
        criado_em=now,
        atualizado_em=now,
    )
    return pedido


def pedido_document(repository, pedido=None, pedido_id=None, with_location=False):
    pedido = pedido or pedido_fixture(pedido_id, with_location)
    document = repository._para_documento(pedido)
    document["_id"] = ObjectId(pedido.id)
    return document


def test_pedidos_repository_serializacao_com_geolocalizacao():
    repository = PedidosRepository.__new__(PedidosRepository)
    pedido = pedido_fixture(with_location=True)

    document = repository._para_documento(pedido)
    document["_id"] = ObjectId(pedido.id)
    location_geojson = dict(document["endereco_entrega"]["localizacao"])
    restored = repository._para_entidade(document)

    assert location_geojson == {
        "type": "Point",
        "coordinates": [-46.63, -23.55],
    }
    assert restored == pedido


async def test_pedidos_repository_indices_insert_remove_e_buscas(monkeypatch):
    collection = Mock()
    collection.create_index = AsyncMock()
    collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
    collection.delete_one = AsyncMock(side_effect=[Mock(deleted_count=0), Mock(deleted_count=1)])
    collection.find_one = AsyncMock(side_effect=[None, None])
    monkeypatch.setattr("app.repositories.pedido_repository.get_mongo_db", lambda: {"pedidos": collection})
    repository = PedidosRepository()

    await repository.criar_indice_historico()
    assert collection.create_index.await_count == 2
    assert await repository.remover("id-invalido") is False
    assert collection.delete_one.await_count == 0
    pedido = pedido_fixture()
    inserted = await repository.inserir(pedido)
    assert inserted.user_id == pedido.user_id
    assert collection.insert_one.await_count == 1
    valid_id = str(ObjectId())
    assert await repository.remover(valid_id) is False
    assert await repository.remover(valid_id) is True
    assert await repository.buscar_por_id("id-invalido") is None
    assert await repository.buscar_por_id(valid_id) is None
    assert await repository.buscar_do_usuario("id-invalido", "user-1") is None
    assert await repository.buscar_do_usuario(valid_id, "user-1") is None
    assert collection.find_one.await_args_list[0].args[0] == {"_id": ObjectId(valid_id)}
    assert collection.find_one.await_args_list[1].args[0] == {"_id": ObjectId(valid_id), "user_id": "user-1"}


async def test_pedidos_repository_lista_historico_admin_e_atualiza_status(monkeypatch):
    oid = ObjectId()
    repository_holder = {}
    user_cursor = AsyncCursor([None])
    all_cursor = AsyncCursor([])
    collection = Mock()
    collection.find = Mock(side_effect=[user_cursor, all_cursor])
    collection.count_documents = AsyncMock(return_value=25)
    collection.find_one_and_update = AsyncMock(return_value=None)
    monkeypatch.setattr("app.repositories.pedido_repository.get_mongo_db", lambda: {"pedidos": collection})
    repository = PedidosRepository()
    repository_holder["repository"] = repository
    document = pedido_document(repository, pedido_id=oid)
    user_cursor.documents = [document]
    all_cursor.documents = [document]

    user_orders = await repository.listar_por_usuario("user-1", pagina=2, limite=5)
    all_orders, total = await repository.listar_todos(pagina=3, limite=10)
    assert len(user_orders) == 1 and user_orders[0].id == str(oid)
    assert len(all_orders) == 1 and total == 25
    assert collection.find.call_args_list[0].args == ({"user_id": "user-1"},)
    assert user_cursor.operations == [("sort", "criado_em", -1), ("skip", 5), ("limit", 5)]
    assert all_cursor.operations == [("sort", "criado_em", -1), ("skip", 20), ("limit", 10)]

    assert await repository.atualizar_status("invalido", StatusPedido.cancelado, datetime.now(timezone.utc)) is None
    assert await repository.atualizar_status(str(oid), StatusPedido.cancelado, datetime.now(timezone.utc)) is None
    collection.find_one_and_update.assert_awaited_once()
    args = collection.find_one_and_update.await_args.kwargs
    assert args["return_document"]


def make_area():
    points = [
        CoordenadaGeografica(longitude=-46.7, latitude=-23.5),
        CoordenadaGeografica(longitude=-46.6, latitude=-23.5),
        CoordenadaGeografica(longitude=-46.6, latitude=-23.4),
        CoordenadaGeografica(longitude=-46.7, latitude=-23.4),
        CoordenadaGeografica(longitude=-46.7, latitude=-23.5),
    ]
    return AreaGeografica(poligonos=[PoligonoGeografico(aneis=[AnelGeografico(pontos=points)])])


def test_zona_repository_serializa_e_desserializa_multi_polygon():
    repository = ZonaEntregaRepository.__new__(ZonaEntregaRepository)
    zona = ZonaEntrega(nome="Centro", valor=4.5, area=make_area())

    document = repository._para_documento(zona)
    restored = repository._para_entidade({**document, "area": {
        "type": "MultiPolygon",
        "coordinates": [document["area"]["coordinates"], document["area"]["coordinates"]],
    }})

    assert document["area"]["type"] == "Polygon"
    assert len(restored.area.poligonos) == 2


async def test_zona_repository_indices_insert_replace_list_and_geo_query(monkeypatch):
    collection = Mock()
    collection.create_index = AsyncMock()
    collection.insert_one = AsyncMock()
    collection.replace_one = AsyncMock()
    collection.delete_one = AsyncMock(side_effect=[Mock(deleted_count=0), Mock(deleted_count=1)])
    cursor = AsyncCursor([])
    collection.find = Mock(return_value=cursor)
    monkeypatch.setattr("app.repositories.zona_entrega_repository.get_mongo_db", lambda: {"zona_entrega": collection})
    repository = ZonaEntregaRepository()
    zona = ZonaEntrega(nome="Centro", valor=4.5, area=make_area())

    await repository.criar_indice_geografico()
    await repository.inserir(zona)
    await repository.atualizar_ou_inserir(zona)
    assert await repository.remover("Centro") is False
    assert await repository.remover("Centro") is True
    assert await repository.listar() == []
    assert await repository.buscar_por_localizacao(CoordenadaGeografica(longitude=-46.65, latitude=-23.45)) == []
    collection.create_index.assert_awaited_once_with([("area", "2dsphere")])
    collection.insert_one.assert_awaited_once_with(repository._para_documento(zona))
    collection.replace_one.assert_awaited_once_with(
        {"nome": "Centro"}, repository._para_documento(zona), upsert=True,
    )
    assert collection.delete_one.await_args_list[0].args == ({"nome": "Centro"},)
    assert collection.find.call_args_list[1].args[0]["area"]["$geoIntersects"]["$geometry"]["type"] == "Point"
