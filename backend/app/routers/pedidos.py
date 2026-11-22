from fastapi import APIRouter, Depends, Query, WebSocket

from app.entities.usuario import Usuario
from app.repositories.pedido_repository import PedidosRepository
from app.repositories.zona_entrega_repository import ZonaEntregaRepository
from app.schemas.pedidos import (
    AtualizarStatus,
    ItemRepetir,
    PedidoCreate,
    PedidoOut,
    PedidosPaginaOut,
)
from app.services.auth_service import AuthService
from app.services.cardapio_service import CardapioService
from app.services.cupom_service import CupomService
from app.services.fidelidade_service import FidelidadeService
from app.services.pedidos_service import PedidoService
from app.services.pedido_eventos_service import PedidoEventosService

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

auth_service = AuthService()
cardapio_service = CardapioService()
pedidos_repository = PedidosRepository()
zona_entrega_repository = ZonaEntregaRepository()
pedido_eventos_service = PedidoEventosService(auth_service)
pedido_service = PedidoService(
    pedidos_repository,
    zona_entrega_repository,
    cardapio_service,
    cupom_service=CupomService(),
    fidelidade_service=FidelidadeService(),
    eventos_service=pedido_eventos_service,
)


def get_pedido_service() -> PedidoService:
    return pedido_service


def get_pedido_eventos_service() -> PedidoEventosService:
    return pedido_eventos_service


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


@router.get(
    "/admin",
    response_model=PedidosPaginaOut,
    dependencies=[Depends(auth_service.usuario_admin)],
)
async def listar_pedidos_admin(
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=50),
    service: PedidoService = Depends(get_pedido_service),
) -> PedidosPaginaOut:
    return await service.listar_admin(pagina, limite)


@router.websocket("/realtime-orders")
async def acompanhar_pedidos(
    websocket: WebSocket,
    token: str = Query(..., min_length=1),
    service: PedidoEventosService = Depends(get_pedido_eventos_service),
) -> None:
    await service.acompanhar(websocket, token)


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
