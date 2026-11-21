from app.entities.payment import PaymentStatus
from app.entities.pedido import StatusPedido
from app.strategy.payment.payment_strategy import PaymentStrategy


class CashPaymentStrategy(PaymentStrategy):
    def status_inicial_pedido(self) -> StatusPedido:
        return StatusPedido.recebido

    def determinar_status(
        self,
        _resultado_simulado: PaymentStatus | None,
    ) -> PaymentStatus:
        return PaymentStatus.pendente
