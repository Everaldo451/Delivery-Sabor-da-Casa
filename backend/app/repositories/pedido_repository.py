from datetime import datetime

from bson import ObjectId
from pymongo import ReturnDocument

from app.database.mongodb import get_mongo_db
from app.entities.pedido import Pedido, StatusPedido
from app.database.mongodb.geojson import (
    coordenada_de_geojson,
    coordenada_para_geojson,
)


def _oid(pedido_id: str) -> ObjectId | None:
    if not ObjectId.is_valid(pedido_id):
        return None
    return ObjectId(pedido_id)


class PedidosRepository:
    def __init__(self) -> None:
        self._collection = get_mongo_db()["pedidos"]

    def _para_entidade(self, doc: dict) -> Pedido:
        dados = {**doc, "id": str(doc["_id"])}
        dados.pop("_id")
        localizacao = dados["endereco_entrega"].get("localizacao")
        if localizacao is not None:
            dados["endereco_entrega"]["localizacao"] = coordenada_de_geojson(
                localizacao
            )
        return Pedido.model_validate(dados)

    def _para_documento(self, pedido: Pedido) -> dict:
        doc = pedido.model_dump(exclude={"id"})
        doc["forma_pagamento"] = pedido.forma_pagamento.value
        doc["status"] = pedido.status.value
        localizacao = pedido.endereco_entrega.localizacao
        if localizacao is None:
            doc["endereco_entrega"].pop("localizacao", None)
        else:
            doc["endereco_entrega"]["localizacao"] = coordenada_para_geojson(
                localizacao
            )
        return doc

    async def criar_indice_historico(self) -> None:
        await self._collection.create_index([("user_id", 1), ("criado_em", -1)])

    async def inserir(self, pedido: Pedido) -> Pedido:
        doc = self._para_documento(pedido)
        resultado = await self._collection.insert_one(doc)
        doc["_id"] = resultado.inserted_id
        return self._para_entidade(doc)

    async def remover(self, pedido_id: str) -> bool:
        oid = _oid(pedido_id)
        if oid is None:
            return False
        resultado = await self._collection.delete_one({"_id": oid})
        return resultado.deleted_count > 0

    async def listar_por_usuario(
        self, usuario_id: str, pagina: int, limite: int
    ) -> list[Pedido]:
        cursor = (
            self._collection.find({"user_id": usuario_id})
            .sort("criado_em", -1)
            .skip((pagina - 1) * limite)
            .limit(limite)
        )
        return [self._para_entidade(doc) async for doc in cursor]

    async def buscar_por_id(self, pedido_id: str) -> Pedido | None:
        oid = _oid(pedido_id)
        if oid is None:
            return None
        doc = await self._collection.find_one({"_id": oid})
        return self._para_entidade(doc) if doc is not None else None

    async def buscar_do_usuario(self, pedido_id: str, usuario_id: str) -> Pedido | None:
        oid = _oid(pedido_id)
        if oid is None:
            return None
        doc = await self._collection.find_one({"_id": oid, "user_id": usuario_id})
        return self._para_entidade(doc) if doc is not None else None

    async def atualizar_status(
        self, pedido_id: str, status: StatusPedido, atualizado_em: datetime
    ) -> Pedido | None:
        oid = _oid(pedido_id)
        if oid is None:
            return None
        doc = await self._collection.find_one_and_update(
            {"_id": oid},
            {"$set": {"status": status.value, "atualizado_em": atualizado_em}},
            return_document=ReturnDocument.AFTER,
        )
        return self._para_entidade(doc) if doc is not None else None
