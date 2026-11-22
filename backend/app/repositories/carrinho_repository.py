from redis.asyncio import Redis

from app.database.redis import redis_client
from app.entities.carrinho import Carrinho


class CarrinhoRepository:
    def __init__(self, client: Redis | None = None) -> None:
        self._client = client if client is not None else redis_client

    async def buscar(self, user_id: str) -> Carrinho | None:
        dados = await self._client.get(self._key(user_id))
        if dados is None:
            return None
        return Carrinho.model_validate_json(dados)

    async def salvar(self, carrinho: Carrinho) -> None:
        await self._client.set(
            self._key(carrinho.user_id),
            carrinho.model_dump_json(),
        )

    async def remover(self, user_id: str) -> None:
        await self._client.delete(self._key(user_id))

    @staticmethod
    def _key(user_id: str) -> str:
        return f"carrinho:{user_id}"
