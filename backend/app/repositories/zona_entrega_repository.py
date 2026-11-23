from app.database.mongodb import get_mongo_db
from app.entities.zona_entrega import ZonaEntrega
from app.database.mongodb.geojson import (
    area_de_geojson,
    area_para_geojson,
    coordenada_para_geojson,
)
from app.types.geografia import CoordenadaGeografica


class ZonaEntregaRepository:
    def __init__(self) -> None:
        self._collection = get_mongo_db()["zona_entrega"]

    def _para_entidade(self, doc: dict) -> ZonaEntrega:
        return ZonaEntrega(
            nome=doc["nome"],
            area=area_de_geojson(doc["area"]),
            valor=doc["valor"],
        )

    def _para_documento(self, zona: ZonaEntrega) -> dict:
        return {
            "nome": zona.nome,
            "area": area_para_geojson(zona.area),
            "valor": zona.valor,
        }

    async def criar_indice_geografico(self) -> None:
        await self._collection.create_index([("area", "2dsphere")])

    async def inserir(self, zona: ZonaEntrega) -> None:
        await self._collection.insert_one(self._para_documento(zona))

    async def atualizar_ou_inserir(self, zona: ZonaEntrega) -> None:
        await self._collection.replace_one(
            {"nome": zona.nome},
            self._para_documento(zona),
            upsert=True,
        )

    async def remover(self, nome: str) -> bool:
        resultado = await self._collection.delete_one({"nome": nome})
        return resultado.deleted_count > 0

    async def listar(self) -> list[ZonaEntrega]:
        cursor = self._collection.find()
        return [self._para_entidade(doc) async for doc in cursor]

    async def buscar_por_localizacao(
        self, localizacao: CoordenadaGeografica
    ) -> list[ZonaEntrega]:
        cursor = self._collection.find(
            {
                "area": {
                    "$geoIntersects": {
                        "$geometry": coordenada_para_geojson(localizacao)
                    }
                }
            }
        )
        return [self._para_entidade(doc) async for doc in cursor]
