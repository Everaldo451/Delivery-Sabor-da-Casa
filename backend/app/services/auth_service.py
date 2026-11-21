"""
PROVISORIO: simula o usuario logado enquanto o modulo de autenticacao nao fica pronto.

Quando o login com JWT estiver pronto, substitua esta dependencia pela validacao do token,
mantendo o atributo `.id` (string) e o atributo `.is_admin` do usuario autenticado.
"""
from fastapi import Header, HTTPException

from app.entities.usuario import Usuario


class AuthService:
    async def usuario_logado(self, x_user_id: str = Header(default="1")) -> Usuario:
        # No Swagger/app de teste: envie X-User-Id para simular usuarios diferentes.
        return Usuario(id=x_user_id)

    async def usuario_admin(self, x_user_id: str = Header(default="1")) -> Usuario:
        usuario = await self.usuario_logado(x_user_id)
        if not usuario.is_admin:
            raise HTTPException(403, "Usuario sem permissao de administrador")
        return usuario
