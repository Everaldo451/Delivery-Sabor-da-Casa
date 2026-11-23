from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.database.mongodb.geojson import area_de_geojson, area_para_geojson
from app.entities.zona_entrega import ZonaEntrega
from app.repositories.zona_entrega_repository import ZonaEntregaRepository
from app.services.auth_service import AuthService
from app.schemas.zonas_entrega import (
    GeoJSONFeatureCollectionIn,
    GeoJSONFeatureCollectionOut,
    GeoJSONFeatureOut,
    ZonaEntregaPropertiesOut,
)

router = APIRouter(prefix="/zonas-entrega", tags=["Zonas de entrega"])
auth_service = AuthService()
zona_repository = ZonaEntregaRepository()


def get_zona_repository() -> ZonaEntregaRepository:
    return zona_repository


def _feature(zona: ZonaEntrega) -> GeoJSONFeatureOut:
    return GeoJSONFeatureOut(
        geometry=area_para_geojson(zona.area),
        properties=ZonaEntregaPropertiesOut(nome=zona.nome, valor=zona.valor),
    )


@router.get("", response_model=GeoJSONFeatureCollectionOut)
async def listar_zonas(
    repository: ZonaEntregaRepository = Depends(get_zona_repository),
) -> GeoJSONFeatureCollectionOut:
    zonas = await repository.listar()
    return GeoJSONFeatureCollectionOut(features=[_feature(zona) for zona in zonas])


@router.post(
    "/importar-geojson",
    response_model=GeoJSONFeatureCollectionOut,
    dependencies=[Depends(auth_service.usuario_admin)],
)
async def importar_geojson(
    dados: GeoJSONFeatureCollectionIn,
    repository: ZonaEntregaRepository = Depends(get_zona_repository),
) -> GeoJSONFeatureCollectionOut:
    zonas: list[ZonaEntrega] = []
    nomes: set[str] = set()

    for indice, feature in enumerate(dados.features, start=1):
        propriedades = feature.properties
        nome = (
            propriedades.get("nome")
            or propriedades.get("zona")
            or propriedades.get("name")
        )
        valor = next(
            (
                propriedades[chave]
                for chave in ("valor", "taxa", "taxa_entrega", "delivery_fee")
                if chave in propriedades
            ),
            None,
        )
        try:
            zona = ZonaEntrega(
                nome=nome,
                area=area_de_geojson(feature.geometry),
                valor=valor,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Feature {indice}: informe um poligono GeoJSON, nome e taxa validos.",
            ) from exc

        if zona.nome in nomes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Feature {indice}: o nome da zona '{zona.nome}' aparece mais de uma vez.",
            )
        nomes.add(zona.nome)
        zonas.append(zona)

    for zona in zonas:
        await repository.atualizar_ou_inserir(zona)

    return GeoJSONFeatureCollectionOut(features=[_feature(zona) for zona in zonas])


@router.delete(
    "/{nome}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth_service.usuario_admin)],
)
async def remover_zona(
    nome: str,
    repository: ZonaEntregaRepository = Depends(get_zona_repository),
) -> Response:
    removida = await repository.remover(nome)
    if not removida:
        raise HTTPException(status_code=404, detail="Zona de entrega nao encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
