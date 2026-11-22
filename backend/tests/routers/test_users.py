from unittest.mock import Mock

from app.routers import users
from app.entities.usuario import Usuario


def test_cadastro_retorna_usuario_sem_hash_de_senha(client):
    service = Mock()
    service.cadastrar.return_value = Usuario(
        id="u-1", nome="Cliente", email="cliente@example.com", senha_hash="segredo"
    )
    client.app.dependency_overrides[users.get_user_service] = lambda: service

    response = client.post(
        "/users",
        json={"nome": "Cliente", "email": "cliente@example.com", "senha": "senha-segura"},
    )

    assert response.status_code == 201
    assert response.json() == {"id": "u-1", "nome": "Cliente", "email": "cliente@example.com"}
    service.cadastrar.assert_called_once()


def test_cadastro_valida_payload(client):
    assert client.post("/users", json={"email": "invalido"}).status_code == 422
