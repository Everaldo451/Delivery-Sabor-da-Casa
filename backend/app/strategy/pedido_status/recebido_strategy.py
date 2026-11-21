from app.entities.pedido import StatusPedido
from app.strategy.pedido_status.pedido_status_strategy import PedidoStatusStrategy


class RecebidoStrategy(PedidoStatusStrategy):
    def permite_transicao(
        self,
        novo_status: StatusPedido,
        _pagamento_aprovado: bool = False,
    ) -> bool:
        return novo_status in (StatusPedido.em_preparo, StatusPedido.cancelado)
