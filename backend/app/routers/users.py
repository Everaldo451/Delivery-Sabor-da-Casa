from fastapi import APIRouter, Depends, status

from app.repositories.user_repository import UserRepository
from app.schemas.users import CadastroUsuario, UsuarioOut
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Usuarios"])

user_repository = UserRepository()
user_service = UserService(user_repository)


def get_user_service() -> UserService:
    return user_service


@router.post(
    "",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_usuario(
    dados: CadastroUsuario,
    service: UserService = Depends(get_user_service),
) -> UsuarioOut:
    usuario = service.cadastrar(dados)
    return UsuarioOut.model_validate(usuario.model_dump())
