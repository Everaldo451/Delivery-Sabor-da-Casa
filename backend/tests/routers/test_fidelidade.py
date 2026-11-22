from decimal import Decimal
from unittest.mock import Mock

from app.entities.fidelidade import SaldoFidelidade
from app.routers import fidelidade


def test_obter_saldo_fidelidade_do_usuario(client):
    service = Mock()
    service.obter_saldo.return_value = SaldoFidelidade(
        user_id="usuario-teste",
        pontos=250,
        valor_resgate_reais=Decimal("2.50"),
    )
    client.app.dependency_overrides[fidelidade.get_fidelidade_service] = lambda: service

    response = client.get("/fidelidade")

    assert response.status_code == 200
    assert response.json()["pontos"] == 250
    assert response.json()["valor_resgate_reais"] == "2.50"
    service.obter_saldo.assert_called_once_with("usuario-teste")


def test_listar_transacoes_vazio(client):
    service = Mock()
    service.listar_transacoes.return_value = []
    client.app.dependency_overrides[fidelidade.get_fidelidade_service] = lambda: service

    response = client.get("/fidelidade/transacoes")

    assert response.status_code == 200
    assert response.json() == []
    service.listar_transacoes.assert_called_once_with("usuario-teste")
