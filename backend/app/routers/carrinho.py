from fastapi import APIRouter, Depends, Response, status

from app.entities.usuario import Usuario
from app.repositories.carrinho_repository import CarrinhoRepository
from app.schemas.carrinho import (
    AtualizarCarrinho,
    AtualizarItemCarrinho,
    CarrinhoOut,
    ItemCarrinhoIn,
)
from app.services.auth_service import AuthService
from app.services.carrinho_service import CarrinhoService

router = APIRouter(prefix="/carrinho", tags=["Carrinho"])

auth_service = AuthService()
carrinho_repository = CarrinhoRepository()
carrinho_service = CarrinhoService(carrinho_repository)


def get_carrinho_service() -> CarrinhoService:
    return carrinho_service


@router.get("", response_model=CarrinhoOut)
async def buscar_carrinho(
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: CarrinhoService = Depends(get_carrinho_service),
) -> CarrinhoOut:
    return await service.buscar(usuario)


@router.put("", response_model=CarrinhoOut)
async def substituir_carrinho(
    dados: AtualizarCarrinho,
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: CarrinhoService = Depends(get_carrinho_service),
) -> CarrinhoOut:
    return await service.substituir(dados, usuario)


@router.post("/itens", response_model=CarrinhoOut)
async def adicionar_item(
    dados: ItemCarrinhoIn,
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: CarrinhoService = Depends(get_carrinho_service),
) -> CarrinhoOut:
    return await service.adicionar(dados, usuario)


@router.patch("/itens/{prato_id}", response_model=CarrinhoOut)
async def atualizar_item(
    prato_id: str,
    dados: AtualizarItemCarrinho,
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: CarrinhoService = Depends(get_carrinho_service),
) -> CarrinhoOut:
    return await service.atualizar_item(prato_id, dados, usuario)


@router.delete("/itens/{prato_id}", response_model=CarrinhoOut)
async def remover_item(
    prato_id: str,
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: CarrinhoService = Depends(get_carrinho_service),
) -> CarrinhoOut:
    return await service.remover_item(prato_id, usuario)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def limpar_carrinho(
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: CarrinhoService = Depends(get_carrinho_service),
) -> Response:
    await service.limpar(usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
