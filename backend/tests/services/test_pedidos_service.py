from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.entities.pedido import FormaPagamento
from app.entities.usuario import Usuario
from app.schemas.pedidos import PedidoCreate
from app.services.pedidos_service import PedidoService


def dados_pedido(**alteracoes) -> PedidoCreate:
    dados = {
        "itens": [{"prato_id": "p-1", "quantidade": 2}],
        "endereco_entrega": {
            "rua": "Rua Teste",
            "numero": "10",
            "bairro": "Centro",
            "cep": "01310-930",
            "localizacao": {"longitude": -46.6, "latitude": -23.5},
        },
        "forma_pagamento": FormaPagamento.pix,
        "cupom_codigo": "BEMVINDO",
        "pontos_resgatados": 200,
    }
    dados.update(alteracoes)
    return PedidoCreate(**dados)


def criar_service():
    pedidos_repository = Mock()
    pedidos_repository.inserir = AsyncMock(
        side_effect=lambda pedido: pedido.model_copy(update={"id": "pedido-mongo-1"})
    )
    pedidos_repository.remover = AsyncMock(return_value=True)
    zona_repository = Mock()
    zona_repository.buscar_por_localizacao = AsyncMock(
        return_value=[SimpleNamespace(valor=5.0)]
    )
    cardapio_service = Mock()
    cardapio_service.buscar_prato = AsyncMock(
        return_value={"id": "p-1", "nome": "Prato", "preco": 20, "disponivel": True}
    )
    cupom_service = Mock()
    cupom_service.calcular_desconto.return_value = Decimal("5.00")
    fidelidade_service = Mock()
    fidelidade_service.calcular_desconto.return_value = Decimal("2.00")
    cep_service = Mock()
    cep_service.verificar_cep = AsyncMock()
    service = PedidoService(
        pedidos_repository,
        zona_repository,
        cardapio_service,
        cupom_service=cupom_service,
        fidelidade_service=fidelidade_service,
        cep_service=cep_service,
    )
    return service, pedidos_repository, cupom_service, fidelidade_service


async def test_criar_pedido_aplica_cupom_e_resgata_pontos():
    service, repository, coupons, loyalty = criar_service()
    service._eventos_service.pedido_criado = AsyncMock()

    pedido = await service.criar_pedido(
        dados_pedido(),
        Usuario(id="u-1", email="u@example.com", senha_hash=""),
    )

    assert pedido.subtotal == 40
    assert pedido.desconto == 7
    assert pedido.total == 38
    assert pedido.cupom_codigo == "BEMVINDO"
    assert pedido.pontos_resgatados == 200
    service._cep_service.verificar_cep.assert_awaited_once_with("01310930")
    coupons.calcular_desconto.assert_called_once_with("BEMVINDO", Decimal("40.00"), "u-1")
    coupons.registrar_uso.assert_called_once_with(
        "BEMVINDO", "u-1", "pedido-mongo-1", Decimal("40.00")
    )
    loyalty.calcular_desconto.assert_called_once_with("u-1", 200, Decimal("35.00"))
    loyalty.resgatar.assert_called_once_with("u-1", "pedido-mongo-1", 200)
    repository.remover.assert_not_awaited()
    service._eventos_service.pedido_criado.assert_awaited_once_with(pedido)


async def test_listar_admin_retorna_metadados_de_paginacao():
    service, repository, _, _ = criar_service()
    repository.listar_todos = AsyncMock(return_value=([], 45))

    pagina = await service.listar_admin(pagina=3, limite=20)

    assert pagina.pedidos == []
    assert pagina.pagina == 3
    assert pagina.limite == 20
    assert pagina.total == 45
    assert pagina.total_paginas == 3
    repository.listar_todos.assert_awaited_once_with(3, 20)


async def test_criar_pedido_remove_documento_se_resgate_atomico_falhar():
    service, repository, coupons, loyalty = criar_service()
    loyalty.resgatar.side_effect = HTTPException(409, "Saldo alterado")

    with pytest.raises(HTTPException) as exc_info:
        await service.criar_pedido(
            dados_pedido(),
            Usuario(id="u-1", email="u@example.com", senha_hash=""),
        )

    assert exc_info.value.status_code == 409
    repository.remover.assert_awaited_once_with("pedido-mongo-1")
    coupons.estornar_uso.assert_called_once_with("pedido-mongo-1")


async def test_criar_pedido_sem_cupom_ou_pontos_nao_consulta_cupom():
    service, _, coupons, loyalty = criar_service()
    loyalty.calcular_desconto.return_value = Decimal("0.00")

    pedido = await service.criar_pedido(
        dados_pedido(cupom_codigo=None, pontos_resgatados=0),
        Usuario(id="u-1", email="u@example.com", senha_hash=""),
    )

    assert pedido.desconto == 0
    assert pedido.total == 45
    coupons.calcular_desconto.assert_not_called()
    loyalty.resgatar.assert_not_called()


async def test_criar_pedido_rejeita_cep_nao_encontrado():
    from app.services.cep_service import CepNaoEncontradoError

    service, repository, _, _ = criar_service()
    service._cep_service.verificar_cep.side_effect = CepNaoEncontradoError

    with pytest.raises(HTTPException) as exc_info:
        await service.criar_pedido(
            dados_pedido(cupom_codigo=None, pontos_resgatados=0),
            Usuario(id="u-1", email="u@example.com", senha_hash=""),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "CEP nao encontrado"
    repository.inserir.assert_not_awaited()


async def test_criar_pedido_retorna_503_se_viacep_indisponivel():
    from app.services.cep_service import ViaCepIndisponivelError

    service, repository, _, _ = criar_service()
    service._cep_service.verificar_cep.side_effect = ViaCepIndisponivelError

    with pytest.raises(HTTPException) as exc_info:
        await service.criar_pedido(
            dados_pedido(cupom_codigo=None, pontos_resgatados=0),
            Usuario(id="u-1", email="u@example.com", senha_hash=""),
        )

    assert exc_info.value.status_code == 503
    repository.inserir.assert_not_awaited()
