from uuid import uuid4

import bcrypt
from fastapi import HTTPException, status

from app.entities.usuario import Usuario
from app.repositories.user_repository import (
    EmailJaCadastradoError,
    UserRepository,
)
from app.schemas.users import CadastroUsuario


class UserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def cadastrar(self, dados: CadastroUsuario) -> Usuario:
        usuario = Usuario(
            id=str(uuid4()),
            nome=dados.nome,
            email=dados.email.strip().casefold(),
            senha_hash=bcrypt.hashpw(
                dados.senha.encode("utf-8"),
                bcrypt.gensalt(),
            ).decode("ascii"),
        )
        try:
            return self._user_repository.inserir(usuario)
        except EmailJaCadastradoError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email ja cadastrado",
            ) from exc
