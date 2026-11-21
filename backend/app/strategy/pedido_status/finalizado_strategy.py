from app.entities.pedido import StatusPedido
from app.strategy.pedido_status.pedido_status_strategy import PedidoStatusStrategy


class FinalizadoStrategy(PedidoStatusStrategy):
    def permite_transicao(
        self,
        _novo_status: StatusPedido,
        _pagamento_aprovado: bool = False,
    ) -> bool:
        return False
