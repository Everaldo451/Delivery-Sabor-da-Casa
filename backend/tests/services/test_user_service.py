from unittest.mock import Mock

import bcrypt
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.entities.usuario import Usuario
from app.repositories.user_repository import EmailJaCadastradoError
from app.schemas.users import CadastroUsuario
from app.services.user_service import UserService


def test_cadastrar_usuario_persiste_nome_email_normalizado_e_hash():
    user_repository = Mock()
    user_repository.inserir.side_effect = lambda usuario: usuario
    service = UserService(user_repository=user_repository)

    resultado = service.cadastrar(
        CadastroUsuario(
            nome="  Cliente Exemplo ",
            email=" CLIENTE@EXAMPLE.COM ",
            senha="senha-segura",
        )
    )

    assert resultado.nome == "Cliente Exemplo"
    assert resultado.email == "cliente@example.com"
    assert bcrypt.checkpw(
        b"senha-segura",
        resultado.senha_hash.encode("ascii"),
    )
    assert isinstance(user_repository.inserir.call_args.args[0], Usuario)


def test_cadastrar_usuario_rejeita_email_duplicado():
    user_repository = Mock()
    user_repository.inserir.side_effect = EmailJaCadastradoError(
        "cliente@example.com"
    )
    service = UserService(user_repository=user_repository)

    with pytest.raises(HTTPException) as exc_info:
        service.cadastrar(
            CadastroUsuario(
                nome="Cliente Exemplo",
                email="cliente@example.com",
                senha="senha-segura",
            )
        )

    assert exc_info.value.status_code == 409


@pytest.mark.parametrize(
    "dados",
    [
        {"nome": "   ", "email": "cliente@example.com", "senha": "senha-segura"},
        {"nome": "Cliente", "email": "cliente@example.com", "senha": "curta"},
        {"nome": "Cliente", "email": "cliente@example.com", "senha": "a" * 73},
    ],
)
def test_cadastro_usuario_valida_nome_e_senha(dados):
    with pytest.raises(ValidationError):
        CadastroUsuario(**dados)
