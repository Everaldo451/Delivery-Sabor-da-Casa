from fastapi import HTTPException

from app.entities.carrinho import Carrinho, ItemCarrinho
from app.entities.usuario import Usuario
from app.repositories.carrinho_repository import CarrinhoRepository
from app.schemas.carrinho import (
    AtualizarCarrinho,
    AtualizarItemCarrinho,
    CarrinhoOut,
    ItemCarrinhoIn,
)


class CarrinhoService:
    def __init__(self, repository: CarrinhoRepository) -> None:
        self._repository = repository

    async def buscar(self, usuario: Usuario) -> CarrinhoOut:
        carrinho = await self._repository.buscar(usuario.id)
        if carrinho is None:
            carrinho = Carrinho(user_id=usuario.id)
        return CarrinhoOut.model_validate(carrinho.model_dump())

    async def substituir(
        self,
        dados: AtualizarCarrinho,
        usuario: Usuario,
    ) -> CarrinhoOut:
        carrinho = Carrinho(
            user_id=usuario.id,
            itens=[ItemCarrinho.model_validate(item) for item in dados.itens],
        )
        await self._repository.salvar(carrinho)
        return CarrinhoOut.model_validate(carrinho.model_dump())

    async def adicionar(
        self,
        dados: ItemCarrinhoIn,
        usuario: Usuario,
    ) -> CarrinhoOut:
        carrinho = await self._obter_ou_criar(usuario.id)
        item_existente = next(
            (item for item in carrinho.itens if item.prato_id == dados.prato_id),
            None,
        )
        if item_existente is None:
            carrinho.itens.append(ItemCarrinho.model_validate(dados.model_dump()))
        else:
            nova_quantidade = item_existente.quantidade + dados.quantidade
            if nova_quantidade > 50:
                raise HTTPException(422, "A quantidade maxima por prato e 50")
            item_existente.quantidade = nova_quantidade
            item_existente.observacao = dados.observacao
        await self._repository.salvar(carrinho)
        return CarrinhoOut.model_validate(carrinho.model_dump())

    async def atualizar_item(
        self,
        prato_id: str,
        dados: AtualizarItemCarrinho,
        usuario: Usuario,
    ) -> CarrinhoOut:
        carrinho = await self._obter_ou_criar(usuario.id)
        item = next(
            (item for item in carrinho.itens if item.prato_id == prato_id),
            None,
        )
        if item is None:
            raise HTTPException(404, "Item nao encontrado no carrinho")
        item.quantidade = dados.quantidade
        item.observacao = dados.observacao
        await self._repository.salvar(carrinho)
        return CarrinhoOut.model_validate(carrinho.model_dump())

    async def remover_item(self, prato_id: str, usuario: Usuario) -> CarrinhoOut:
        carrinho = await self._obter_ou_criar(usuario.id)
        itens = [item for item in carrinho.itens if item.prato_id != prato_id]
        if len(itens) == len(carrinho.itens):
            raise HTTPException(404, "Item nao encontrado no carrinho")
        carrinho.itens = itens
        await self._repository.salvar(carrinho)
        return CarrinhoOut.model_validate(carrinho.model_dump())

    async def limpar(self, usuario: Usuario) -> None:
        await self._repository.remover(usuario.id)

    async def _obter_ou_criar(self, user_id: str) -> Carrinho:
        carrinho = await self._repository.buscar(user_id)
        if carrinho is None:
            return Carrinho(user_id=user_id)
        return carrinho
