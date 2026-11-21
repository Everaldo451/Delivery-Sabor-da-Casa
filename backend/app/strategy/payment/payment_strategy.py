from abc import ABC, abstractmethod

from app.entities.payment import PaymentStatus


class PaymentStrategy(ABC):
    @abstractmethod
    def status_inicial_pedido(self) -> StatusPedido:
        raise NotImplementedError

    @abstractmethod
    def determinar_status(
        self,
        resultado_simulado: PaymentStatus | None,
    ) -> PaymentStatus:
        raise NotImplementedError
