from unittest.mock import AsyncMock

from app.entities.carrinho import Carrinho, ItemCarrinho
from app.repositories.carrinho_repository import CarrinhoRepository


async def test_buscar_desserializa_carrinho_e_usa_chave_por_usuario():
    client = AsyncMock()
    client.get.return_value = '{"user_id":"u-1","itens":[]}'
    repository = CarrinhoRepository(client)

    resultado = await repository.buscar("u-1")

    assert resultado == Carrinho(user_id="u-1", itens=[])
    client.get.assert_awaited_once_with("carrinho:u-1")


async def test_buscar_retorna_none_quando_nao_existe_chave():
    client = AsyncMock()
    client.get.return_value = None

    resultado = await CarrinhoRepository(client).buscar("u-sem-carrinho")

    assert resultado is None
    client.get.assert_awaited_once_with("carrinho:u-sem-carrinho")


async def test_salvar_aplica_ttl_de_24_horas():
    client = AsyncMock()
    repository = CarrinhoRepository(client)
    carrinho = Carrinho(user_id="u-2", itens=[ItemCarrinho(prato_id="p-1", quantidade=1)])

    await repository.salvar(carrinho)

    args = client.set.await_args
    assert args.args[0] == "carrinho:u-2"
    assert args.kwargs["ex"] == 86400
    assert Carrinho.model_validate_json(args.args[1]) == carrinho


async def test_remover_apaga_chave_do_usuario():
    client = AsyncMock()
    await CarrinhoRepository(client).remover("u-3")
    client.delete.assert_awaited_once_with("carrinho:u-3")
