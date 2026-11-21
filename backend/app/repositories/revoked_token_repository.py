from datetime import datetime

from redis.asyncio import Redis

from app.database.redis import redis_client


class RevokedTokenRepository:
    def __init__(self, client: Redis | None = None) -> None:
        self._client = client if client is not None else redis_client

    async def contem(self, jti: str) -> bool:
        return bool(await self._client.exists(self._key(jti)))

    async def inserir(self, jti: str, expires_at: datetime) -> None:
        await self._client.set(
            self._key(jti),
            "1",
            exat=int(expires_at.timestamp()),
        )

    @staticmethod
    def _key(jti: str) -> str:
        return f"auth:revoked:{jti}"
