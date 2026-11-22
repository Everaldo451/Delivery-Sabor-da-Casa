from decimal import Decimal
from unittest.mock import Mock

from app.entities.cupom import Cupom, TipoDescontoCupom
from app.routers import cupons


def test_listar_cupons_ativos(client):
    service = Mock()
    service.listar.return_value = [
        Cupom(
            id=1,
            codigo="BEMVINDO",
            descricao="Desconto de boas-vindas",
            tipo=TipoDescontoCupom.percentual,
            valor=Decimal("10"),
        )
    ]
    client.app.dependency_overrides[cupons.get_cupom_service] = lambda: service

    response = client.get("/cupons")

    assert response.status_code == 200
    assert response.json()[0]["codigo"] == "BEMVINDO"


def test_listar_todos_cupons_para_administracao(client):
    service = Mock()
    service.listar_todos.return_value = []
    client.app.dependency_overrides[cupons.get_cupom_service] = lambda: service

    response = client.get("/cupons/admin")

    assert response.status_code == 200
    assert response.json() == []
    service.listar_todos.assert_called_once()


def test_validar_cupom_calcula_desconto(client):
    service = Mock()
    service.calcular_desconto.return_value = Decimal("10.00")
    client.app.dependency_overrides[cupons.get_cupom_service] = lambda: service

    response = client.post(
        "/cupons/validar",
        json={"codigo": " bemvindo ", "subtotal": "100.00"},
    )

    assert response.status_code == 200
    assert response.json() == {"codigo": "BEMVINDO", "desconto": "10.00"}
    service.calcular_desconto.assert_called_once_with("BEMVINDO", Decimal("100.00"), "usuario-teste")


def test_criar_cupom_como_admin(client):
    service = Mock()
    service.criar.return_value = Cupom(
        id=2,
        codigo="NOVO10",
        descricao="Desconto promocional",
        tipo=TipoDescontoCupom.percentual,
        valor=Decimal("10"),
    )
    client.app.dependency_overrides[cupons.get_cupom_service] = lambda: service

    response = client.post("/cupons", json={
        "codigo": " novo10 ",
        "descricao": "Desconto promocional",
        "tipo": "percentual",
        "valor": "10",
    })

    assert response.status_code == 201
    assert response.json()["codigo"] == "NOVO10"
    service.criar.assert_called_once()


def test_cupom_invalido_retorna_422(client):
    response = client.post("/cupons", json={"codigo": "??", "valor": -1})
    assert response.status_code == 422
