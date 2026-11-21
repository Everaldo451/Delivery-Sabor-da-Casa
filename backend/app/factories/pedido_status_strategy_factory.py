from app.entities.pedido import StatusPedido
from app.strategy.pedido_status.aguardando_pagamento_strategy import (
    AguardandoPagamentoStrategy,
)
from app.strategy.pedido_status.em_preparo_strategy import EmPreparoStrategy
from app.strategy.pedido_status.finalizado_strategy import FinalizadoStrategy
from app.strategy.pedido_status.pedido_status_strategy import PedidoStatusStrategy
from app.strategy.pedido_status.recebido_strategy import RecebidoStrategy
from app.strategy.pedido_status.saiu_para_entrega_strategy import (
    SaiuParaEntregaStrategy,
)


class PedidoStatusStrategyFactory:
    def __init__(self) -> None:
        finalizado = FinalizadoStrategy()
        self._strategies: dict[StatusPedido, PedidoStatusStrategy] = {
            StatusPedido.aguardando_pagamento: AguardandoPagamentoStrategy(),
            StatusPedido.recebido: RecebidoStrategy(),
            StatusPedido.em_preparo: EmPreparoStrategy(),
            StatusPedido.saiu_para_entrega: SaiuParaEntregaStrategy(),
            StatusPedido.entregue: finalizado,
            StatusPedido.cancelado: finalizado,
        }

    def criar(self, status_atual: StatusPedido) -> PedidoStatusStrategy:
        try:
            return self._strategies[status_atual]
        except KeyError as exc:
            raise ValueError(f"Status de pedido nao suportado: {status_atual}") from exc
