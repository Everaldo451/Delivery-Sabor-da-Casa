from unittest.mock import AsyncMock

from app.entities.zona_entrega import ZonaEntrega
from app.routers import zonas_entrega
from app.types.geografia import (
    AnelGeografico,
    AreaGeografica,
    CoordenadaGeografica,
    PoligonoGeografico,
)


def make_zone(name="Centro", value=4.5):
    points = [
        CoordenadaGeografica(longitude=-46.7, latitude=-23.5),
        CoordenadaGeografica(longitude=-46.6, latitude=-23.5),
        CoordenadaGeografica(longitude=-46.6, latitude=-23.4),
        CoordenadaGeografica(longitude=-46.7, latitude=-23.4),
        CoordenadaGeografica(longitude=-46.7, latitude=-23.5),
    ]
    return ZonaEntrega(
        nome=name,
        valor=value,
        area=AreaGeografica(poligonos=[PoligonoGeografico(aneis=[AnelGeografico(pontos=points)])]),
    )


def feature(name="Centro", value=4.5):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[-46.7, -23.5], [-46.6, -23.5], [-46.6, -23.4], [-46.7, -23.4], [-46.7, -23.5]]],
        },
        "properties": {"nome": name, "valor": value},
    }


def test_listar_zonas_retorna_feature_collection(client, app):
    repository = type("Repository", (), {"listar": AsyncMock(return_value=[make_zone()])})()
    app.dependency_overrides[zonas_entrega.get_zona_repository] = lambda: repository

    response = client.get("/zonas-entrega")

    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert response.json()["features"][0]["properties"] == {"nome": "Centro", "valor": 4.5}


def test_import_geojson_upserts_zones(client, app):
    repository = type("Repository", (), {"atualizar_ou_inserir": AsyncMock()})()
    app.dependency_overrides[zonas_entrega.get_zona_repository] = lambda: repository

    response = client.post("/zonas-entrega/importar-geojson", json={"type": "FeatureCollection", "features": [feature()]})

    assert response.status_code == 200
    assert response.json()["features"][0]["properties"] == {"nome": "Centro", "valor": 4.5}
    repository.atualizar_ou_inserir.assert_awaited_once()


def test_import_geojson_aceita_propriedades_do_seed(client, app):
    repository = type("Repository", (), {"atualizar_ou_inserir": AsyncMock()})()
    app.dependency_overrides[zonas_entrega.get_zona_repository] = lambda: repository
    seed_feature = feature()
    seed_feature["properties"] = {"zona": "Centro", "taxa": 4.5}

    response = client.post("/zonas-entrega/importar-geojson", json={"type": "FeatureCollection", "features": [seed_feature]})

    assert response.status_code == 200
    assert response.json()["features"][0]["properties"]["nome"] == "Centro"


def test_import_geojson_invalido_nao_grava_parcialmente(client, app):
    repository = type("Repository", (), {"atualizar_ou_inserir": AsyncMock()})()
    app.dependency_overrides[zonas_entrega.get_zona_repository] = lambda: repository
    invalid = feature()
    invalid["geometry"] = {"type": "Point", "coordinates": [1, 2]}

    response = client.post("/zonas-entrega/importar-geojson", json={"type": "FeatureCollection", "features": [feature(), invalid]})

    assert response.status_code == 422
    repository.atualizar_ou_inserir.assert_not_awaited()


def test_import_geojson_rejeita_nome_duplicado(client, app):
    repository = type("Repository", (), {"atualizar_ou_inserir": AsyncMock()})()
    app.dependency_overrides[zonas_entrega.get_zona_repository] = lambda: repository

    response = client.post("/zonas-entrega/importar-geojson", json={"type": "FeatureCollection", "features": [feature(), feature()]})

    assert response.status_code == 422
    repository.atualizar_ou_inserir.assert_not_awaited()


def test_remover_zona_responde_204_ou_404(client, app):
    repository = type("Repository", (), {"remover": AsyncMock(side_effect=[True, False])})()
    app.dependency_overrides[zonas_entrega.get_zona_repository] = lambda: repository

    assert client.delete("/zonas-entrega/Centro").status_code == 204
    assert client.delete("/zonas-entrega/ausente").status_code == 404
