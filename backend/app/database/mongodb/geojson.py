from app.types.geografia import (
    AnelGeografico,
    AreaGeografica,
    CoordenadaGeografica,
    PoligonoGeografico,
)


def coordenada_para_geojson(coordenada: CoordenadaGeografica) -> dict:
    return {
        "type": "Point",
        "coordinates": [coordenada.longitude, coordenada.latitude],
    }


def coordenada_de_geojson(geometria: dict) -> CoordenadaGeografica:
    if geometria["type"] != "Point":
        raise ValueError("Esperava geometria GeoJSON do tipo Point")
    longitude, latitude = geometria["coordinates"]
    return CoordenadaGeografica(longitude=longitude, latitude=latitude)


def area_para_geojson(area: AreaGeografica) -> dict:
    poligonos = [
        [
            [
                [ponto.longitude, ponto.latitude]
                for ponto in anel.pontos
            ]
            for anel in poligono.aneis
        ]
        for poligono in area.poligonos
    ]
    if len(poligonos) == 1:
        return {"type": "Polygon", "coordinates": poligonos[0]}
    return {"type": "MultiPolygon", "coordinates": poligonos}


def area_de_geojson(geometria: dict) -> AreaGeografica:
    tipo = geometria["type"]
    coordenadas = geometria["coordinates"]
    if tipo == "Polygon":
        coordenadas = [coordenadas]
    elif tipo != "MultiPolygon":
        raise ValueError("Esperava geometria GeoJSON do tipo Polygon ou MultiPolygon")

    return AreaGeografica(
        poligonos=[
            PoligonoGeografico(
                aneis=[
                    AnelGeografico(
                        pontos=[
                            CoordenadaGeografica(
                                longitude=longitude,
                                latitude=latitude,
                            )
                            for longitude, latitude in anel
                        ]
                    )
                    for anel in poligono
                ]
            )
            for poligono in coordenadas
        ]
    )
