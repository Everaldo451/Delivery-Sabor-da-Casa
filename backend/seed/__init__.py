import asyncio
import json
from pathlib import Path

from app.database.mongodb import client
from app.database.mongodb.geojson import area_de_geojson
from app.entities.zona_entrega import ZonaEntrega
from app.repositories.zona_entrega_repository import ZonaEntregaRepository

ARQUIVO_ZONAS = Path(__file__).parent / "mongodb" / "zonas_jp.json"


def carregar_zonas() -> list[ZonaEntrega]:
    dados = json.loads(ARQUIVO_ZONAS.read_text(encoding="utf-8-sig"))
    if dados.get("type") != "FeatureCollection":
        raise ValueError("O arquivo de zonas deve ser uma FeatureCollection GeoJSON")

    features = dados.get("features")
    if not isinstance(features, list) or len(features) != 7:
        raise ValueError("O arquivo zonas_jp.json deve conter exatamente 7 zonas")

    zonas = []
    for indice, feature in enumerate(features, start=1):
        if feature.get("type") != "Feature":
            raise ValueError(f"Feature invalida na posicao {indice}")

        propriedades = feature.get("properties")
        geometria = feature.get("geometry")
        if not isinstance(propriedades, dict) or not isinstance(geometria, dict):
            raise ValueError(f"Dados incompletos na zona da posicao {indice}")
        if "zona" not in propriedades or "taxa" not in propriedades:
            raise ValueError(f"Nome ou taxa ausente na zona da posicao {indice}")

        zonas.append(
            ZonaEntrega(
                nome=propriedades["zona"],
                area=area_de_geojson(geometria),
                valor=propriedades["taxa"],
            )
        )

    return zonas


async def seed_zonas() -> int:
    zonas = carregar_zonas()
    repository = ZonaEntregaRepository()
    await repository.criar_indice_geografico()
    for zona in zonas:
        await repository.atualizar_ou_inserir(zona)
    return len(zonas)


def main() -> None:
    try:
        total = asyncio.run(seed_zonas())
        print(f"{total} zonas de entrega importadas/atualizadas.")
    finally:
        client.close()


if __name__ == "__main__":
    main()