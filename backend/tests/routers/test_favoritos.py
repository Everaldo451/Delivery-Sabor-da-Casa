from datetime import datetime, timezone
from unittest.mock import Mock

from app.entities.favorito import Favorito
from app.routers import favoritos


def test_listar_favoritos_do_usuario(client):
    service = Mock()
    service.listar.return_value = [
        Favorito(
            user_id="usuario-teste",
            prato_id="prato-1",
            criado_em=datetime.now(timezone.utc),
        )
    ]
    client.app.dependency_overrides[favoritos.get_favorito_service] = lambda: service

    response = client.get("/favoritos")

    assert response.status_code == 200
    assert response.json()[0]["prato_id"] == "prato-1"
    service.listar.assert_called_once_with("usuario-teste")


def test_adicionar_favorito_e_idempotente_na_rota(client):
    service = Mock()
    service.adicionar.return_value = Favorito(
        user_id="usuario-teste",
        prato_id="prato-1",
        criado_em=datetime.now(timezone.utc),
    )
    client.app.dependency_overrides[favoritos.get_favorito_service] = lambda: service

    response = client.put("/favoritos/prato-1")

    assert response.status_code == 200
    assert response.json()["prato_id"] == "prato-1"
    service.adicionar.assert_called_once_with("usuario-teste", "prato-1")


def test_remover_favorito_retorna_204(client):
    service = Mock()
    client.app.dependency_overrides[favoritos.get_favorito_service] = lambda: service

    response = client.delete("/favoritos/prato-1")

    assert response.status_code == 204
    service.remover.assert_called_once_with("usuario-teste", "prato-1")
