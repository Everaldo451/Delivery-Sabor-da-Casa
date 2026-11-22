from fastapi import APIRouter, Body, Depends, Response, status

from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticacao"])
auth_service = AuthService()


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest) -> TokenResponse:
    return auth_service.login(dados)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(dados: RefreshTokenRequest) -> TokenResponse:
    return await auth_service.refresh(dados.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    dados: LogoutRequest | None = Body(default=None),
    token: str = Depends(auth_service.obter_token),
) -> Response:
    await auth_service.logout(
        token,
        dados.refresh_token if dados is not None else None,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
