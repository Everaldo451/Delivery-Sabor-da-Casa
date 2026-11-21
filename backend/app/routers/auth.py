from fastapi import APIRouter, Depends, Response, status

from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticacao"])
auth_service = AuthService()


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest) -> TokenResponse:
    return auth_service.login(dados)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(token: str = Depends(auth_service.obter_token)) -> Response:
    await auth_service.logout(token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
