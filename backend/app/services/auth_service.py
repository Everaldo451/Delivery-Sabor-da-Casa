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

        agora = datetime.now(timezone.utc)
        expiracao = agora + ACCESS_TOKEN_DURATION
        token = jwt.encode(
            {
                "sub": usuario.id,
                "iat": agora,
                "exp": expiracao,
                "jti": str(uuid4()),
            },
            self._jwt_secret(),
            algorithm=JWT_ALGORITHM,
        )
        return TokenResponse(
            access_token=token,
            expires_in=int(ACCESS_TOKEN_DURATION.total_seconds()),
        )

    async def logout(self, token: str) -> None:
        _, claims = await self._validar_token(token)
        expiracao = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        await self._revoked_token_repository.inserir(claims["jti"], expiracao)

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
        self, token: str
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
        if await self._revoked_token_repository.contem(jti):
            raise self._erro_autenticacao()

        usuario = self._user_repository.buscar_por_id(subject)
        if usuario is None:
            raise self._erro_autenticacao()
        return usuario, claims

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
