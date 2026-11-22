from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

from app.repositories.revoked_token_repository import RevokedTokenRepository


async def test_inserir_define_expiracao_do_jwt_no_redis():
    redis_client = Mock()
    redis_client.set = AsyncMock()
    expiracao = datetime.now(timezone.utc) + timedelta(minutes=10)
    repository = RevokedTokenRepository(redis_client)

    await repository.inserir("jti-1", expiracao)

    redis_client.set.assert_awaited_once_with(
        "auth:revoked:jti-1",
        "1",
        exat=int(expiracao.timestamp()),
    )


async def test_contem_consulta_se_o_token_esta_revogado_no_redis():
    redis_client = Mock()
    redis_client.exists = AsyncMock(return_value=1)
    repository = RevokedTokenRepository(redis_client)

    resultado = await repository.contem("jti-1")

    assert resultado is True
    redis_client.exists.assert_awaited_once_with("auth:revoked:jti-1")


async def test_inserir_se_ausente_faz_consumo_atomico_do_refresh_token():
    redis_client = Mock()
    redis_client.set = AsyncMock(return_value=True)
    expiracao = datetime.now(timezone.utc) + timedelta(days=7)
    repository = RevokedTokenRepository(redis_client)

    resultado = await repository.inserir_se_ausente("refresh-1", expiracao)

    assert resultado is True
    redis_client.set.assert_awaited_once_with(
        "auth:revoked:refresh-1",
        "1",
        exat=int(expiracao.timestamp()),
        nx=True,
    )
