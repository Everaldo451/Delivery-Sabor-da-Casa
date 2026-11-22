import httpx
import pytest

from app.services.cep_service import (
    CepNaoEncontradoError,
    ViaCepIndisponivelError,
    ViaCepService,
)


async def test_verifica_cep_existente_via_viacep():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"cep": "01310-930"})
    )
    async with httpx.AsyncClient(transport=transport) as client:
        await ViaCepService(client).verificar_cep("01310930")


async def test_cep_inexistente_retorna_erro_de_dominio():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"erro": "true"})
    )
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(CepNaoEncontradoError):
            await ViaCepService(client).verificar_cep("99999999")


async def test_indisponibilidade_do_viacep_e_tratada():
    def falhar(request):
        raise httpx.ConnectError("sem conexao", request=request)

    transport = httpx.MockTransport(falhar)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ViaCepIndisponivelError):
            await ViaCepService(client).verificar_cep("01310930")


def test_endereco_normaliza_cep_com_mascara():
    from app.entities.pedido import EnderecoEntrega

    endereco = EnderecoEntrega(
        rua="Rua Teste",
        numero="10",
        bairro="Centro",
        cep="01310-930",
    )

    assert endereco.cep == "01310930"


def test_endereco_rejeita_cep_com_formato_invalido():
    from pydantic import ValidationError

    from app.entities.pedido import EnderecoEntrega

    with pytest.raises(ValidationError):
        EnderecoEntrega(
            rua="Rua Teste",
            numero="10",
            bairro="Centro",
            cep="0131A-930",
        )


def test_criacao_de_pedido_exige_cep():
    from pydantic import ValidationError

    from app.schemas.pedidos import PedidoCreate

    with pytest.raises(ValidationError, match="CEP do endereco de entrega obrigatorio"):
        PedidoCreate(
            itens=[{"prato_id": "prato-1", "quantidade": 1}],
            endereco_entrega={"rua": "Rua Teste", "numero": "10", "bairro": "Centro"},
            forma_pagamento="pix",
        )
