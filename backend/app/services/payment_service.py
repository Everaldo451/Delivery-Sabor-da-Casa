from decimal import Decimal

from fastapi import HTTPException

from app.entities.payment import Payment, PaymentStatus
from app.entities.usuario import Usuario
from app.factories.payment_strategy_factory import PaymentStrategyFactory
from app.repositories.payment_repository import PaymentRepository
from app.repositories.pedido_repository import PedidosRepository
from app.schemas.payments import CheckoutCreate, PaymentOut
from app.services.pedidos_service import PedidoService


class PaymentService:
    def __init__(
        self,
        payment_repository: PaymentRepository,
        pedidos_repository: PedidosRepository,
        pedido_service: PedidoService,
        payment_strategy_factory: PaymentStrategyFactory | None = None,
    ) -> None:
        self._payment_repository = payment_repository
        self._pedidos_repository = pedidos_repository
        self._payment_strategy_factory = (
            payment_strategy_factory or PaymentStrategyFactory()
        )
        self._pedido_service = pedido_service

    def _para_saida(self, payment: Payment) -> PaymentOut:
        if payment.id is None:
            raise ValueError("Pagamento sem identificador persistido")
        return PaymentOut.model_validate(payment.model_dump())

    async def checkout(
        self,
        dados: CheckoutCreate,
        usuario: Usuario,
    ) -> PaymentOut:
        pedido = await self._pedidos_repository.buscar_do_usuario(
            dados.pedido_id,
            usuario.id,
        )
        if pedido is None:
            raise HTTPException(404, "Pedido nao encontrado")
        if dados.method != pedido.forma_pagamento:
            raise HTTPException(409, "Forma de pagamento diferente do pedido")

        strategy = self._payment_strategy_factory.criar(pedido.forma_pagamento)
        status = strategy.determinar_status(dados.simulation_result)
        simulation_result = (
            status.value
            if status in (PaymentStatus.aprovado, PaymentStatus.recusado)
            else None
        )

        payment = Payment(
            pedido_id=pedido.id,
            user_id=usuario.id,
            amount=Decimal(str(pedido.total)),
            method=dados.method,
            status=status,
            simulation_result=simulation_result,
        )
        payment = self._payment_repository.inserir(payment)

        if status == PaymentStatus.aprovado:
            await self._pedido_service.confirmar_pagamento(dados.pedido_id)

        return self._para_saida(payment)

    def listar(
        self,
        usuario: Usuario,
    ) -> list[PaymentOut]:
        payments = self._payment_repository.listar_por_usuario(usuario.id)
        return [self._para_saida(payment) for payment in payments]

    def buscar(
        self,
        payment_id: int,
        usuario: Usuario,
    ) -> PaymentOut:
        payment = self._payment_repository.buscar_por_id(payment_id)
        if payment is None or payment.user_id != usuario.id:
            raise HTTPException(404, "Pagamento nao encontrado")
        return self._para_saida(payment)
