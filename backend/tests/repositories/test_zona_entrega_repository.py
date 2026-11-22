from app.entities.zona_entrega import ZonaEntrega
from app.repositories.zona_entrega_repository import ZonaEntregaRepository
from app.types.geografia import (
    AnelGeografico,
    AreaGeografica,
    CoordenadaGeografica,
    PoligonoGeografico,
)


def test_zona_de_entrega_serializa_e_desserializa_geojson():
    zona = ZonaEntrega(
        nome="Centro", valor=4.5,
        area=AreaGeografica(poligonos=[PoligonoGeografico(aneis=[AnelGeografico(
            pontos=[
                CoordenadaGeografica(longitude=-46.7, latitude=-23.5),
                CoordenadaGeografica(longitude=-46.6, latitude=-23.5),
                CoordenadaGeografica(longitude=-46.6, latitude=-23.4),
                CoordenadaGeografica(longitude=-46.7, latitude=-23.4),
                CoordenadaGeografica(longitude=-46.7, latitude=-23.5),
            ]
        )])]),
    )
    repository = ZonaEntregaRepository.__new__(ZonaEntregaRepository)

    doc = repository._para_documento(zona)
    restored = repository._para_entidade(doc)

    assert doc["area"]["type"] == "Polygon"
    assert restored.nome == zona.nome
    assert restored.area == zona.area
    assert restored.valor == zona.valor
