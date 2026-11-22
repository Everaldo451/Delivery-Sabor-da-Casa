from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.entities.payment import Payment, PaymentStatus
from app.entities.pedido import (
    EnderecoEntrega,
    FormaPagamento,
    ItemPedido,
    Pedido,
    StatusPedido,
)
from app.entities.usuario import Usuario
from app.schemas.payments import CheckoutCreate
from app.schemas.pedidos import AtualizarStatus
from app.services.pedidos_service import PedidoService
from app.services.payment_service import PaymentService


def pedido_teste(
    method: FormaPagamento,
    status: StatusPedido,
) -> Pedido:
    agora = datetime.now(timezone.utc)
    return Pedido(
        id="pedido-1",
        user_id="1",
        itens=[
            ItemPedido(
                prato_id="prato-1",
                nome="Prato teste",
                preco_unitario=30,
                quantidade=1,
            )
        ],
        subtotal=30,
        desconto=0,
        taxa_entrega=5,
        total=35,
        endereco_entrega=EnderecoEntrega(
            rua="Rua Teste",
            numero="10",
            bairro="Centro",
        ),
        forma_pagamento=method,
        status=status,
        criado_em=agora,
        atualizado_em=agora,
    )


@pytest.mark.parametrize(
    (
        "method",
        "resultado",
        "status",
        "simulation_result",
        "status_pedido_inicial",
        "status_pedido_apos_pagamento",
    ),
    [
        (
            FormaPagamento.pix,
            PaymentStatus.aprovado,
            PaymentStatus.aprovado,
            "aprovado",
            StatusPedido.aguardando_pagamento,
            StatusPedido.recebido,
        ),
        (
            FormaPagamento.pix,
            PaymentStatus.recusado,
            PaymentStatus.recusado,
            "recusado",
            StatusPedido.aguardando_pagamento,
            None,
        ),
        (
            FormaPagamento.cartao,
            PaymentStatus.aprovado,
            PaymentStatus.aprovado,
            "aprovado",
            StatusPedido.aguardando_pagamento,
            StatusPedido.recebido,
        ),
        (
            FormaPagamento.dinheiro,
            PaymentStatus.aprovado,
            PaymentStatus.pendente,
            None,
            StatusPedido.recebido,
            None,
        ),
        (
            FormaPagamento.dinheiro,
            PaymentStatus.recusado,
            PaymentStatus.pendente,
            None,
            StatusPedido.recebido,
            None,
        ),
    ],
)
async def test_checkout_usa_strategy_de_pagamento(
    method,
    resultado,
    status,
    simulation_result,
    status_pedido_inicial,
    status_pedido_apos_pagamento,
):
    pedidos_repository = Mock()
    pedidos_repository.buscar_do_usuario = AsyncMock(
        return_value=pedido_teste(method, status_pedido_inicial)
    )
    pedidos_repository.buscar_por_id = AsyncMock(
        return_value=pedido_teste(method, status_pedido_inicial)
    )
    pedidos_repository.atualizar_status = AsyncMock(
        return_value=pedido_teste(method, StatusPedido.recebido)
    )

    payment_repository = Mock()
    payment_repository.inserir.return_value = Payment(
        id=1,
        pedido_id="pedido-1",
        user_id="1",
        amount=Decimal("35.00"),
        method=method,
        status=status,
        simulation_result=simulation_result,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    pedido_service = PedidoService(
        pedidos_repository,
        Mock(),
        Mock(),
    )
    service = PaymentService(
        payment_repository,
        pedidos_repository,
        pedido_service,
    )

    saida = await service.checkout(
        CheckoutCreate(
            pedido_id="pedido-1",
            method=method,
            simulation_result=resultado,
        ),
        Usuario(id="1", email="cliente@example.com", senha_hash=""),
    )

    assert saida.status == status
    payment_repository.inserir.assert_called_once()
    payment = payment_repository.inserir.call_args.args[0]
    assert payment.status == status
    assert payment.simulation_result == simulation_result
    if status_pedido_apos_pagamento is None:
        pedidos_repository.atualizar_status.assert_not_awaited()
    else:
        pedidos_repository.atualizar_status.assert_awaited_once()
        assert (
            pedidos_repository.atualizar_status.call_args.args[1]
            == status_pedido_apos_pagamento
        )


async def test_pedido_aguardando_pagamento_nao_avanca_para_preparo():
    pedidos_repository = Mock()
    pedidos_repository.buscar_por_id = AsyncMock(
        return_value=pedido_teste(
            FormaPagamento.pix,
            StatusPedido.aguardando_pagamento,
        )
    )
    pedidos_repository.atualizar_status = AsyncMock()
    service = PedidoService(
        pedidos_repository,
        Mock(),
        Mock(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.atualizar_status(
            "pedido-1",
            AtualizarStatus(status=StatusPedido.em_preparo),
        )

    assert exc_info.value.status_code == 409
    pedidos_repository.atualizar_status.assert_not_awaited()


async def test_pedido_aguardando_pagamento_nao_e_confirmado_manualmente():
    pedidos_repository = Mock()
    pedidos_repository.buscar_por_id = AsyncMock(
        return_value=pedido_teste(
            FormaPagamento.pix,
            StatusPedido.aguardando_pagamento,
        )
    )
    pedidos_repository.atualizar_status = AsyncMock()
    service = PedidoService(
        pedidos_repository,
        Mock(),
        Mock(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.atualizar_status(
            "pedido-1",
            AtualizarStatus(status=StatusPedido.recebido),
        )

    assert exc_info.value.status_code == 409
    pedidos_repository.atualizar_status.assert_not_awaited()


async def test_pedido_recebido_pode_ser_cancelado_antes_do_preparo():
    pedidos_repository = Mock()
    pedidos_repository.buscar_por_id = AsyncMock(
        return_value=pedido_teste(
            FormaPagamento.dinheiro,
            StatusPedido.recebido,
        )
    )
    pedidos_repository.atualizar_status = AsyncMock(
        return_value=pedido_teste(
            FormaPagamento.dinheiro,
            StatusPedido.cancelado,
        )
    )
    service = PedidoService(
        pedidos_repository,
        Mock(),
        Mock(),
    )

    resultado = await service.atualizar_status(
        "pedido-1",
        AtualizarStatus(status=StatusPedido.cancelado),
    )

    assert resultado.status == StatusPedido.cancelado
    pedidos_repository.atualizar_status.assert_awaited_once()


async def test_pedido_em_preparo_nao_pode_ser_cancelado():
    pedidos_repository = Mock()
    pedidos_repository.buscar_por_id = AsyncMock(
        return_value=pedido_teste(
            FormaPagamento.dinheiro,
            StatusPedido.em_preparo,
        )
    )
    pedidos_repository.atualizar_status = AsyncMock()
    service = PedidoService(
        pedidos_repository,
        Mock(),
        Mock(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.atualizar_status(
            "pedido-1",
            AtualizarStatus(status=StatusPedido.cancelado),
        )

    assert exc_info.value.status_code == 409
    pedidos_repository.atualizar_status.assert_not_awaited()
