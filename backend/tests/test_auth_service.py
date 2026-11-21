import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import bcrypt
import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from app.entities.usuario import Usuario
from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService, JWT_ALGORITHM


JWT_SECRET = "test-secret-key-with-at-least-32-bytes"


def test_entidade_usuario_nao_serializa_hash_da_senha():
    usuario = Usuario(
        id="usuario-1",
        email="cliente@example.com",
        senha_hash="hash-secreto",
    )

    assert usuario.senha_hash == "hash-secreto"
    assert "senha_hash" not in usuario.model_dump()


def _token(usuario_id: str = "usuario-1", jti: str = "token-1") -> str:
    agora = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": usuario_id,
            "jti": jti,
            "iat": agora,
            "exp": agora + timedelta(minutes=5),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def test_login_emite_jwt_para_credenciais_validas(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", JWT_SECRET)
    user_repository = Mock()
    user_repository.buscar_por_email.return_value = Usuario(
        id="usuario-1",
        email="cliente@example.com",
        senha_hash=bcrypt.hashpw(b"senha-correta", bcrypt.gensalt()).decode("ascii"),
        is_admin=True,
    )
    service = AuthService(user_repository=user_repository)

    resultado = service.login(
        LoginRequest(email=" CLIENTE@EXAMPLE.COM ", senha="senha-correta")
    )

    claims = jwt.decode(
        resultado.access_token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )
    assert claims["sub"] == "usuario-1"
    assert resultado.token_type == "bearer"
    assert resultado.expires_in == 1800
    user_repository.buscar_por_email.assert_called_once_with("cliente@example.com")


def test_login_rejeita_senha_incorreta(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", JWT_SECRET)
    user_repository = Mock()
    user_repository.buscar_por_email.return_value = Usuario(
        id="usuario-1",
        email="cliente@example.com",
        senha_hash=bcrypt.hashpw(b"senha-correta", bcrypt.gensalt()).decode("ascii"),
    )
    service = AuthService(user_repository=user_repository)

    with pytest.raises(HTTPException) as exc_info:
        service.login(LoginRequest(email="cliente@example.com", senha="errada"))

    assert exc_info.value.status_code == 401


def test_login_rejeita_senha_acima_do_limite_bcrypt():
    with pytest.raises(ValidationError):
        LoginRequest(email="cliente@example.com", senha="a" * 73)


def test_logout_revoga_token_e_usuario_logado_rejeita_reuso(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", JWT_SECRET)
    user_repository = Mock()
    user_repository.buscar_por_id.return_value = Usuario(
        id="usuario-1",
        email="cliente@example.com",
        senha_hash="",
    )
    revoked_token_repository = Mock()
    revoked_token_repository.contem = AsyncMock(return_value=False)
    revoked_token_repository.inserir = AsyncMock()
    service = AuthService(
        user_repository=user_repository,
        revoked_token_repository=revoked_token_repository,
    )
    token = _token()
    credenciais = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    asyncio.run(service.logout(token))

    revoked_token_repository.inserir.assert_awaited_once()
    assert revoked_token_repository.inserir.call_args.args[0] == "token-1"
    assert revoked_token_repository.inserir.call_args.args[1].tzinfo == timezone.utc
    revoked_token_repository.contem.return_value = True
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.usuario_logado(credenciais))
    assert exc_info.value.status_code == 401
