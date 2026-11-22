import os
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any
from uuid import uuid4

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.entities.usuario import Usuario
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_DURATION = timedelta(minutes=30)
REFRESH_TOKEN_DURATION = timedelta(days=7)
bearer_scheme = HTTPBearer(auto_error=False)


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository | None = None,
        revoked_token_repository: RevokedTokenRepository | None = None,
    ) -> None:
        self._user_repository = user_repository or UserRepository()
        self._revoked_token_repository = (
            revoked_token_repository or RevokedTokenRepository()
        )

    def login(self, dados: LoginRequest) -> TokenResponse:
        email = dados.email.strip().casefold()
        usuario = self._user_repository.buscar_por_email(email)
        hash_senha = (
            usuario.senha_hash.encode("ascii")
            if usuario is not None
            else self._hash_senha_invalida()
        )
        senha_valida = bcrypt.checkpw(dados.senha.encode("utf-8"), hash_senha)

        if usuario is None or not senha_valida:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return self._emitir_tokens(usuario)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        usuario, claims = await self._validar_token(
            refresh_token,
            tipo_esperado="refresh",
        )
        expiracao = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        consumido = await self._revoked_token_repository.inserir_se_ausente(
            claims["jti"],
            expiracao,
        )
        if not consumido:
            raise self._erro_autenticacao()
        return self._emitir_tokens(usuario)

    async def logout(
        self,
        token: str,
        refresh_token: str | None = None,
    ) -> None:
        usuario, access_claims = await self._validar_token(
            token,
            tipo_esperado="access",
        )
        refresh_claims = None
        if refresh_token is not None:
            usuario_refresh, refresh_claims = await self._validar_token(
                refresh_token,
                tipo_esperado="refresh",
            )
            if usuario_refresh.id != usuario.id:
                raise self._erro_autenticacao()

        await self._revogar(access_claims)
        if refresh_claims is not None:
            await self._revogar(refresh_claims)

    async def usuario_logado(
        self,
        credenciais: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> Usuario:
        token = self._exigir_token(credenciais)
        usuario, _ = await self._validar_token(token)
        return usuario

    async def usuario_admin(
        self,
        credenciais: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> Usuario:
        usuario = await self.usuario_logado(credenciais)
        if not usuario.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario sem permissao de administrador",
            )
        return usuario

    def obter_token(
        self,
        credenciais: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> str:
        return self._exigir_token(credenciais)

    async def _validar_token(
        self,
        token: str,
        tipo_esperado: str = "access",
    ) -> tuple[Usuario, dict[str, Any]]:
        try:
            claims = jwt.decode(
                token,
                self._jwt_secret(),
                algorithms=[JWT_ALGORITHM],
                options={"require": ["exp", "iat", "sub", "jti"]},
            )
        except jwt.InvalidTokenError as exc:
            raise self._erro_autenticacao() from exc

        subject = claims.get("sub")
        jti = claims.get("jti")
        if not isinstance(subject, str) or not isinstance(jti, str):
            raise self._erro_autenticacao()
        # Tokens anteriores à introdução de refresh não tinham este claim;
        # continuam válidos como access tokens até expirarem.
        tipo_token = claims.get("token_type", "access")
        if tipo_token != tipo_esperado:
            raise self._erro_autenticacao()
        if await self._revoked_token_repository.contem(jti):
            raise self._erro_autenticacao()

        usuario = self._user_repository.buscar_por_id(subject)
        if usuario is None:
            raise self._erro_autenticacao()
        return usuario, claims

    def _emitir_tokens(self, usuario: Usuario) -> TokenResponse:
        agora = datetime.now(timezone.utc)
        access_token = self._criar_token(
            usuario.id,
            agora,
            ACCESS_TOKEN_DURATION,
            "access",
        )
        refresh_token = self._criar_token(
            usuario.id,
            agora,
            REFRESH_TOKEN_DURATION,
            "refresh",
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(ACCESS_TOKEN_DURATION.total_seconds()),
            refresh_expires_in=int(REFRESH_TOKEN_DURATION.total_seconds()),
        )

    @staticmethod
    def _criar_token(
        usuario_id: str,
        emitido_em: datetime,
        duracao: timedelta,
        tipo: str,
    ) -> str:
        return jwt.encode(
            {
                "sub": usuario_id,
                "iat": emitido_em,
                "exp": emitido_em + duracao,
                "jti": str(uuid4()),
                "token_type": tipo,
            },
            AuthService._jwt_secret(),
            algorithm=JWT_ALGORITHM,
        )

    async def _revogar(self, claims: dict[str, Any]) -> None:
        expiracao = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        await self._revoked_token_repository.inserir(claims["jti"], expiracao)

    @staticmethod
    def _exigir_token(
        credenciais: HTTPAuthorizationCredentials | None,
    ) -> str:
        if credenciais is None:
            raise AuthService._erro_autenticacao()
        return credenciais.credentials

    @staticmethod
    def _jwt_secret() -> str:
        secret = os.getenv("JWT_SECRET_KEY", "")
        if len(secret.encode("utf-8")) < 32:
            raise RuntimeError(
                "JWT_SECRET_KEY deve conter pelo menos 32 bytes aleatorios"
            )
        return secret

    @staticmethod
    @lru_cache(maxsize=1)
    def _hash_senha_invalida() -> bytes:
        return bcrypt.hashpw(secrets.token_bytes(32), bcrypt.gensalt())

    @staticmethod
    def _erro_autenticacao() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas ou token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
