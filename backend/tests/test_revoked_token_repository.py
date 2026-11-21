import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

from app.repositories.revoked_token_repository import RevokedTokenRepository


def test_inserir_define_expiracao_do_jwt_no_redis():
    redis_client = Mock()
    redis_client.set = AsyncMock()
    expiracao = datetime.now(timezone.utc) + timedelta(minutes=10)
    repository = RevokedTokenRepository(redis_client)

    asyncio.run(repository.inserir("jti-1", expiracao))

    redis_client.set.assert_awaited_once_with(
        "auth:revoked:jti-1",
        "1",
        exat=int(expiracao.timestamp()),
    )


def test_contem_consulta_se_o_token_esta_revogado_no_redis():
    redis_client = Mock()
    redis_client.exists = AsyncMock(return_value=1)
    repository = RevokedTokenRepository(redis_client)

    resultado = asyncio.run(repository.contem("jti-1"))

    assert resultado is True
    redis_client.exists.assert_awaited_once_with("auth:revoked:jti-1")
