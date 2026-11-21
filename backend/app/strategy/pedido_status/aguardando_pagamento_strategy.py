from app.entities.pedido import StatusPedido
from app.strategy.pedido_status.pedido_status_strategy import PedidoStatusStrategy


class AguardandoPagamentoStrategy(PedidoStatusStrategy):
    def permite_transicao(
        self,
        novo_status: StatusPedido,
        pagamento_aprovado: bool = False,
    ) -> bool:
        if novo_status == StatusPedido.cancelado:
            return True
        return (
            novo_status == StatusPedido.recebido
            and pagamento_aprovado
        )
