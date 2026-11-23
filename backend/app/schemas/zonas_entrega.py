from typing import Any, Literal

from pydantic import BaseModel


class GeoJSONFeatureIn(BaseModel):
    type: Literal["Feature"]
    geometry: dict[str, Any]
    properties: dict[str, Any]


class GeoJSONFeatureCollectionIn(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[GeoJSONFeatureIn]


class ZonaEntregaPropertiesOut(BaseModel):
    nome: str
    valor: float


class GeoJSONFeatureOut(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any]
    properties: ZonaEntregaPropertiesOut


class GeoJSONFeatureCollectionOut(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[GeoJSONFeatureOut]
