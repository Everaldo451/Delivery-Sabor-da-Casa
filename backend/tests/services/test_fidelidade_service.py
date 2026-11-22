from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.services.fidelidade_service import FidelidadeService


def test_valor_de_resgate_equivale_a_um_centavo_por_ponto():
    repository = Mock()
    repository.saldo.return_value = 325

    saldo = FidelidadeService(repository).obter_saldo("u-1")

    assert saldo.pontos == 325
    assert saldo.valor_resgate_reais == Decimal("3.25")


def test_calcula_desconto_em_pontos():
    repository = Mock()
    repository.saldo.return_value = 500

    desconto = FidelidadeService(repository).calcular_desconto(
        "u-1", 250, Decimal("10.00")
    )

    assert desconto == Decimal("2.50")


@pytest.mark.parametrize(
    ("saldo", "pontos", "subtotal"),
    [(50, 100, Decimal("10")), (500, 2000, Decimal("10"))],
)
def test_rejeita_resgate_sem_saldo_ou_acima_do_subtotal(saldo, pontos, subtotal):
    repository = Mock()
    repository.saldo.return_value = saldo

    with pytest.raises(HTTPException) as exc_info:
        FidelidadeService(repository).calcular_desconto("u-1", pontos, subtotal)

    assert exc_info.value.status_code == 422


def test_acumula_um_ponto_por_real_pago():
    repository = Mock()
    repository.creditar_por_pedido.return_value = 48

    resultado = FidelidadeService(repository).creditar_por_pedido(
        "u-1", "pedido-1", Decimal("48.90")
    )

    assert resultado == 48
    repository.creditar_por_pedido.assert_called_once_with("u-1", "pedido-1", 48)
