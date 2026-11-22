from datetime import datetime, timezone
from decimal import Decimal
from app.database.postgresql.models.payment import PaymentModel
from app.entities.payment import Payment, PaymentStatus
from app.entities.pedido import FormaPagamento
from app.repositories.payment_repository import PaymentRepository


def test_converte_model_de_pagamento_para_entidade():
    now = datetime.now(timezone.utc)
    model = PaymentModel(
        id=7, pedido_id="pedido-1", user_id="u-1", amount=Decimal("15.00"),
        method=FormaPagamento.pix, status=PaymentStatus.aprovado,
        simulation_result="aprovado", created_at=now, updated_at=now,
    )

    result = PaymentRepository()._para_entidade(model)

    assert result == Payment(
        id=7, pedido_id="pedido-1", user_id="u-1", amount=Decimal("15.00"),
        method=FormaPagamento.pix, status=PaymentStatus.aprovado,
        simulation_result="aprovado", created_at=now, updated_at=now,
    )


def test_converte_entidade_de_pagamento_para_model():
    payment = Payment(
        pedido_id="pedido-1", user_id="u-1", amount=Decimal("15.00"),
        method=FormaPagamento.pix, status=PaymentStatus.pendente,
    )
    model = PaymentRepository()._para_modelo(payment)
    assert model.pedido_id == payment.pedido_id
    assert model.method == payment.method
    assert model.amount == payment.amount
