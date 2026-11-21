from abc import ABC, abstractmethod

from app.entities.pedido import StatusPedido


class PedidoStatusStrategy(ABC):
    @abstractmethod
    def permite_transicao(
        self,
        novo_status: StatusPedido,
        pagamento_aprovado: bool = False,
    ) -> bool:
        raise NotImplementedError
