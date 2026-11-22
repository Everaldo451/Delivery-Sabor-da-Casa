from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.entities.cupom import Cupom, TipoDescontoCupom
from app.schemas.cupons import CupomCreate
from app.services.cupom_service import CupomService


def test_calcula_desconto_percentual_com_limite():
    repository = Mock()
    repository.buscar_por_codigo.return_value = Cupom(
        id=1,
        codigo="DEZ",
        descricao="Dez por cento",
        tipo=TipoDescontoCupom.percentual,
        valor=Decimal("10"),
        desconto_maximo=Decimal("8.00"),
    )
    repository.validar_disponibilidade.return_value = None

    desconto = CupomService(repository).calcular_desconto(
        " dez ", Decimal("100.00"), "u-1"
    )

    assert desconto == Decimal("8.00")
    repository.buscar_por_codigo.assert_called_once_with("DEZ")


def test_calcula_desconto_fixo_sem_exceder_subtotal():
    repository = Mock()
    repository.buscar_por_codigo.return_value = Cupom(
        id=2,
        codigo="FIXO",
        descricao="Valor fixo",
        tipo=TipoDescontoCupom.valor_fixo,
        valor=Decimal("20.00"),
    )

    repository.validar_disponibilidade.return_value = None
    assert CupomService(repository).calcular_desconto(
        "FIXO", Decimal("12.50"), "u-1"
    ) == Decimal("12.50")


@pytest.mark.parametrize(
    ("ativo", "subtotal_minimo", "valido_ate", "subtotal"),
    [
        (False, Decimal("0"), None, Decimal("100")),
        (True, Decimal("50"), None, Decimal("20")),
        (True, Decimal("0"), date.today() - timedelta(days=1), Decimal("100")),
    ],
)
def test_rejeita_cupom_inativo_minimo_ou_expirado(
    ativo,
    subtotal_minimo,
    valido_ate,
    subtotal,
):
    repository = Mock()
    repository.buscar_por_codigo.return_value = Cupom(
        id=3,
        codigo="TESTE",
        descricao="Cupom de teste",
        tipo=TipoDescontoCupom.valor_fixo,
        valor=Decimal("5"),
        ativo=ativo,
        subtotal_minimo=subtotal_minimo,
        valido_ate=valido_ate,
    )
    repository.validar_disponibilidade.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        CupomService(repository).calcular_desconto("TESTE", subtotal, "u-1")

    assert exc_info.value.status_code == 422


def test_rejeita_cupom_indisponivel_para_usuario():
    from app.repositories.cupom_repository import UsoCupomIndisponivelError

    repository = Mock()
    repository.buscar_por_codigo.return_value = Cupom(
        id=9,
        codigo="LIMITE",
        descricao="Uso limitado",
        tipo=TipoDescontoCupom.valor_fixo,
        valor=Decimal("5"),
    )
    repository.validar_disponibilidade.side_effect = UsoCupomIndisponivelError(
        "Limite total de usos do cupom atingido"
    )

    with pytest.raises(HTTPException) as exc_info:
        CupomService(repository).calcular_desconto("LIMITE", Decimal("20"), "u-1")

    assert exc_info.value.status_code == 422
    assert "Limite total" in exc_info.value.detail


def test_criar_normaliza_codigo_e_converte_duplicidade():
    repository = Mock()
    repository.inserir.side_effect = lambda cupom: cupom.model_copy(update={"id": 5})
    service = CupomService(repository)
    dados = CupomCreate(
        codigo="  novo10 ",
        descricao="Promocao",
        tipo=TipoDescontoCupom.percentual,
        valor=Decimal("10"),
    )

    criado = service.criar(dados)

    assert criado.codigo == "NOVO10"
    assert criado.id == 5
