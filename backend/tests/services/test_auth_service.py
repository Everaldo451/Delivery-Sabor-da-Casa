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
from app.services.auth_service import (
    ACCESS_TOKEN_DURATION,
    REFRESH_TOKEN_DURATION,
    AuthService,
    JWT_ALGORITHM,
)


JWT_SECRET = "test-secret-key-with-at-least-32-bytes"


def test_entidade_usuario_nao_serializa_hash_da_senha():
    usuario = Usuario(
        id="usuario-1",
        email="cliente@example.com",
        senha_hash="hash-secreto",
    )

    assert usuario.senha_hash == "hash-secreto"
    assert "senha_hash" not in usuario.model_dump()


def _token(
    usuario_id: str = "usuario-1",
    jti: str = "token-1",
    token_type: str | None = "access",
) -> str:
    agora = datetime.now(timezone.utc)
    claims = {
        "sub": usuario_id,
        "jti": jti,
        "iat": agora,
        "exp": agora + timedelta(minutes=5),
    }
    if token_type is not None:
        claims["token_type"] = token_type
    return jwt.encode(
        claims,
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
    refresh_claims = jwt.decode(
        resultado.refresh_token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )
    assert claims["sub"] == "usuario-1"
    assert claims["token_type"] == "access"
    assert refresh_claims["token_type"] == "refresh"
    assert refresh_claims["sub"] == "usuario-1"
    assert resultado.token_type == "bearer"
    assert resultado.expires_in == 1800
    assert resultado.refresh_expires_in == int(REFRESH_TOKEN_DURATION.total_seconds())
    assert resultado.expires_in == int(ACCESS_TOKEN_DURATION.total_seconds())
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


async def test_logout_revoga_token_e_usuario_logado_rejeita_reuso(monkeypatch):
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

    await service.logout(token)

    revoked_token_repository.inserir.assert_awaited_once()
    assert revoked_token_repository.inserir.call_args.args[0] == "token-1"
    assert revoked_token_repository.inserir.call_args.args[1].tzinfo == timezone.utc
    revoked_token_repository.contem.return_value = True
    with pytest.raises(HTTPException) as exc_info:
        await service.usuario_logado(credenciais)
    assert exc_info.value.status_code == 401


async def test_refresh_rotaciona_refresh_token_e_emite_novo_par(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", JWT_SECRET)
    usuario = Usuario(
        id="usuario-1",
        email="cliente@example.com",
        senha_hash="",
    )
    user_repository = Mock()
    user_repository.buscar_por_id.return_value = usuario
    revoked_token_repository = Mock()
    revoked_token_repository.contem = AsyncMock(return_value=False)
    revoked_token_repository.inserir_se_ausente = AsyncMock(return_value=True)
    service = AuthService(user_repository, revoked_token_repository)
    refresh_token = _token(token_type="refresh")

    resultado = await service.refresh(refresh_token)

    claims_antigas = jwt.decode(
        refresh_token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )
    access_claims = jwt.decode(
        resultado.access_token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )
    refresh_claims = jwt.decode(
        resultado.refresh_token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )
    revoked_token_repository.inserir_se_ausente.assert_awaited_once_with(
        claims_antigas["jti"],
        datetime.fromtimestamp(claims_antigas["exp"], tz=timezone.utc),
    )
    assert access_claims["token_type"] == "access"
    assert refresh_claims["token_type"] == "refresh"
    assert access_claims["jti"] != refresh_claims["jti"]
    assert access_claims["exp"] - access_claims["iat"] == int(
        ACCESS_TOKEN_DURATION.total_seconds()
    )
    assert refresh_claims["exp"] - refresh_claims["iat"] == int(
        REFRESH_TOKEN_DURATION.total_seconds()
    )


async def test_refresh_rejeita_access_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", JWT_SECRET)
    repository = Mock()
    repository.buscar_por_id.return_value = Usuario(
        id="usuario-1", email="cliente@example.com", senha_hash=""
    )
    revoked = Mock()
    revoked.contem = AsyncMock(return_value=False)
    revoked.inserir = AsyncMock()
    service = AuthService(repository, revoked)

    with pytest.raises(HTTPException) as exc_info:
        await service.refresh(_token(token_type="access"))

    assert exc_info.value.status_code == 401
    revoked.inserir.assert_not_awaited()


async def test_access_token_legacy_sem_tipo_continua_autenticando(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", JWT_SECRET)
    usuario = Usuario(
        id="usuario-1", email="cliente@example.com", senha_hash=""
    )
    repository = Mock()
    repository.buscar_por_id.return_value = usuario
    revoked = Mock()
    revoked.contem = AsyncMock(return_value=False)
    service = AuthService(repository, revoked)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=_token(token_type=None),
    )

    assert await service.usuario_logado(credentials) == usuario


async def test_refresh_rejeita_token_revogado(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", JWT_SECRET)
    repository = Mock()
    repository.buscar_por_id.return_value = Usuario(
        id="usuario-1", email="cliente@example.com", senha_hash=""
    )
    revoked = Mock()
    revoked.contem = AsyncMock(return_value=True)
    revoked.inserir = AsyncMock()
    service = AuthService(repository, revoked)

    with pytest.raises(HTTPException) as exc_info:
        await service.refresh(_token(token_type="refresh"))

    assert exc_info.value.status_code == 401
    revoked.inserir.assert_not_awaited()


async def test_refresh_rejeita_reutilizacao_concorrente(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", JWT_SECRET)
    repository = Mock()
    repository.buscar_por_id.return_value = Usuario(
        id="usuario-1", email="cliente@example.com", senha_hash=""
    )
    revoked = Mock()
    revoked.contem = AsyncMock(return_value=False)
    revoked.inserir_se_ausente = AsyncMock(return_value=False)
    service = AuthService(repository, revoked)

    with pytest.raises(HTTPException) as exc_info:
        await service.refresh(_token(token_type="refresh"))

    assert exc_info.value.status_code == 401


async def test_logout_revoga_access_e_refresh_token_da_sessao(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", JWT_SECRET)
    repository = Mock()
    repository.buscar_por_id.return_value = Usuario(
        id="usuario-1", email="cliente@example.com", senha_hash=""
    )
    revoked = Mock()
    revoked.contem = AsyncMock(return_value=False)
    revoked.inserir = AsyncMock()
    revoked.inserir_se_ausente = AsyncMock(return_value=True)
    service = AuthService(repository, revoked)

    await service.logout(
        _token(jti="access-1", token_type="access"),
        _token(jti="refresh-1", token_type="refresh"),
    )

    assert [call.args[0] for call in revoked.inserir.await_args_list] == [
        "access-1",
        "refresh-1",
    ]


async def test_logout_nao_revoga_refresh_de_outro_usuario(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", JWT_SECRET)
    repository = Mock()
    repository.buscar_por_id.side_effect = [
        Usuario(id="usuario-1", email="um@example.com", senha_hash=""),
        Usuario(id="usuario-2", email="dois@example.com", senha_hash=""),
    ]
    revoked = Mock()
    revoked.contem = AsyncMock(return_value=False)
    revoked.inserir = AsyncMock()
    service = AuthService(repository, revoked)

    with pytest.raises(HTTPException) as exc_info:
        await service.logout(
            _token(usuario_id="usuario-1", jti="access-1"),
            _token(usuario_id="usuario-2", jti="refresh-2", token_type="refresh"),
        )

    assert exc_info.value.status_code == 401
    revoked.inserir.assert_not_awaited()
