from fastapi import APIRouter, Depends, HTTPException, Query

from app.entities.usuario import Usuario
from app.schemas.enderecos import SugestaoEnderecoOut
from app.services.auth_service import AuthService
from app.services.geocodificacao_service import (
    GeocodificacaoIndisponivelError,
    PhotonService,
)

router = APIRouter(prefix="/enderecos", tags=["Enderecos"])
auth_service = AuthService()
photon_service = PhotonService()


def get_photon_service() -> PhotonService:
    return photon_service


@router.get("/sugestoes", response_model=list[SugestaoEnderecoOut])
async def sugerir_enderecos(
    q: str = Query(min_length=5, max_length=180),
    _: Usuario = Depends(auth_service.usuario_logado),
    service: PhotonService = Depends(get_photon_service),
) -> list[SugestaoEnderecoOut]:
    try:
        sugestoes = await service.sugerir_enderecos(q.strip())
    except GeocodificacaoIndisponivelError as exc:
        raise HTTPException(503, "Busca de endereco indisponivel") from exc
    return [SugestaoEnderecoOut.model_validate(item) for item in sugestoes]
