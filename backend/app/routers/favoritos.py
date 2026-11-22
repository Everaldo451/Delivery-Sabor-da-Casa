from fastapi import APIRouter, Depends, Response, status

from app.entities.usuario import Usuario
from app.schemas.favoritos import FavoritoOut
from app.services.auth_service import AuthService
from app.services.favorito_service import FavoritoService

router = APIRouter(prefix="/favoritos", tags=["Favoritos"])
auth_service = AuthService()
favorito_service = FavoritoService()


def get_favorito_service() -> FavoritoService:
    return favorito_service


@router.get("", response_model=list[FavoritoOut])
def listar_favoritos(
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: FavoritoService = Depends(get_favorito_service),
) -> list[FavoritoOut]:
    return service.listar(usuario.id)


@router.put("/{prato_id}", response_model=FavoritoOut)
def adicionar_favorito(
    prato_id: str,
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: FavoritoService = Depends(get_favorito_service),
) -> FavoritoOut:
    return FavoritoOut.model_validate(
        service.adicionar(usuario.id, prato_id).model_dump()
    )


@router.delete("/{prato_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_favorito(
    prato_id: str,
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: FavoritoService = Depends(get_favorito_service),
) -> Response:
    service.remover(usuario.id, prato_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
