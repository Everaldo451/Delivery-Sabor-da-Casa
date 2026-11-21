"""
PROVISORIO: simula o usuario logado enquanto o modulo de autenticacao nao fica pronto.

Quando o login com JWT estiver pronto, substitua esta dependencia pela validacao do token,
mantendo o atributo `.id` (string) e o atributo `.is_admin` do usuario autenticado.
"""
from fastapi import Header

from app.entities.usuario import Usuario


class AuthService:
    async def usuario_logado(self, x_user_id: str = Header(default="1")) -> Usuario:
        # No Swagger/app de teste: envie X-User-Id para simular usuarios diferentes.
        return Usuario(id=x_user_id)
