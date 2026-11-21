from app.entities.pedido import FormaPagamento
from app.strategy.payment.card_payment_strategy import CardPaymentStrategy
from app.strategy.payment.cash_payment_strategy import CashPaymentStrategy
from app.strategy.payment.payment_strategy import PaymentStrategy
from app.strategy.payment.pix_payment_strategy import PixPaymentStrategy


class PaymentStrategyFactory:
    def __init__(self) -> None:
        self._strategies: dict[FormaPagamento, PaymentStrategy] = {
            FormaPagamento.pix: PixPaymentStrategy(),
            FormaPagamento.cartao: CardPaymentStrategy(),
            FormaPagamento.dinheiro: CashPaymentStrategy(),
        }

    def criar(self, forma_pagamento: FormaPagamento) -> PaymentStrategy:
        try:
            return self._strategies[forma_pagamento]
        except KeyError as exc:
            raise ValueError(
                f"Forma de pagamento nao suportada: {forma_pagamento}"
            ) from exc
