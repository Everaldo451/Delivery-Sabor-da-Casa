from fastapi import APIRouter, Depends

from app.entities.usuario import Usuario
from app.repositories.payment_repository import PaymentRepository
from app.repositories.pedido_repository import PedidosRepository
from app.routers.pedidos import get_pedido_service
from app.schemas.payments import CheckoutCreate, PaymentOut
from app.services.auth_service import AuthService
from app.services.payment_service import PaymentService

router = APIRouter(tags=["Checkout"])

auth_service = AuthService()
payment_repository = PaymentRepository()
pedido_repository = PedidosRepository()
payment_service = PaymentService(
    payment_repository,
    pedido_repository,
    get_pedido_service(),
)


def get_payment_service() -> PaymentService:
    return payment_service


@router.post("/checkout", response_model=PaymentOut, status_code=201)
async def checkout(
    dados: CheckoutCreate,
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: PaymentService = Depends(get_payment_service),
):
    return await service.checkout(dados, usuario)


@router.get("/payments", response_model=list[PaymentOut])
def listar_payments(
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: PaymentService = Depends(get_payment_service),
):
    return service.listar(usuario)


@router.get("/payments/{payment_id}", response_model=PaymentOut)
def detalhe_payment(
    payment_id: int,
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: PaymentService = Depends(get_payment_service),
):
    return service.buscar(payment_id, usuario)
