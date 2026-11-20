"""
PROVISORIO: simula o usuario logado enquanto o modulo de autenticacao nao fica pronto.

Quando o colega entregar o login com JWT, troque o corpo de `usuario_logado` pela dependencia
dele (que valida o token e devolve o usuario). Mantenha o nome `usuario_logado` e o atributo
`.id` (string) e o resto do codigo de pedidos nao precisa mudar.
"""
from fastapi import Header
from pydantic import BaseModel


class Usuario(BaseModel):
    id: str


async def usuario_logado(x_user_id: str = Header(default="1")) -> Usuario:
    # No Swagger/app de teste: envie o header X-User-Id para simular usuarios diferentes
    return Usuario(id=x_user_id)
