from fastapi import APIRouter, Depends, Query

from app.entities.usuario import Usuario
from app.repositories.pedido_repository import PedidosRepository
from app.repositories.zona_entrega_repository import ZonaEntregaRepository
from app.schemas.pedidos import (
    AtualizarStatus,
    ItemRepetir,
    PedidoCreate,
    PedidoOut,
)
from app.services.auth_service import AuthService
from app.services.cardapio_service import CardapioService
from app.services.pedidos_service import PedidoService

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

auth_service = AuthService()
cardapio_service = CardapioService()
pedidos_repository = PedidosRepository()
zona_entrega_repository = ZonaEntregaRepository()
pedido_service = PedidoService(
    pedidos_repository,
    zona_entrega_repository,
    cardapio_service,
)


def get_pedido_service() -> PedidoService:
    return pedido_service


@router.post("", response_model=PedidoOut, status_code=201)
async def criar_pedido(
    dados: PedidoCreate,
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: PedidoService = Depends(get_pedido_service),
):
    return await service.criar_pedido(dados, usuario)


@router.get("", response_model=list[PedidoOut])
async def historico(
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=50),
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: PedidoService = Depends(get_pedido_service),
):
    return await service.historico(pagina, limite, usuario)


@router.get("/{pedido_id}", response_model=PedidoOut)
async def detalhe_pedido(
    pedido_id: str,
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: PedidoService = Depends(get_pedido_service),
):
    return await service.detalhe_pedido(pedido_id, usuario)


@router.get("/{pedido_id}/repetir", response_model=list[ItemRepetir])
async def itens_para_repetir(
    pedido_id: str,
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: PedidoService = Depends(get_pedido_service),
):
    return await service.itens_para_repetir(pedido_id, usuario)


@router.patch(
    "/{pedido_id}/status",
    response_model=PedidoOut,
    dependencies=[Depends(auth_service.usuario_admin)],
)
async def atualizar_status(
    pedido_id: str,
    dados: AtualizarStatus,
    service: PedidoService = Depends(get_pedido_service),
):
    return await service.atualizar_status(pedido_id, dados)
