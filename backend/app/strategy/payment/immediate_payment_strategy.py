from app.entities.payment import PaymentStatus
from app.entities.pedido import StatusPedido
from app.strategy.payment.payment_strategy import PaymentStrategy


class ImmediatePaymentStrategy(PaymentStrategy):
    def status_inicial_pedido(self) -> StatusPedido:
        return StatusPedido.aguardando_pagamento

    def determinar_status(
        self,
        resultado_simulado: PaymentStatus | None,
    ) -> PaymentStatus:
        if resultado_simulado == PaymentStatus.recusado:
            return PaymentStatus.recusado
        return PaymentStatus.aprovado
