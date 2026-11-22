from unittest.mock import AsyncMock

from app.routers import auth
from app.schemas.auth import LoginRequest, TokenResponse


def test_login_retorna_token(client, monkeypatch):
    monkeypatch.setattr(
        auth.auth_service,
        "login",
        lambda dados: TokenResponse(access_token="jwt-teste", expires_in=1800),
    )

    response = client.post(
        "/auth/login",
        json={"email": "cliente@example.com", "senha": "senha-segura"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "jwt-teste"


def test_logout_revoga_token_do_bearer(client, monkeypatch):
    logout = AsyncMock()
    monkeypatch.setattr(auth.auth_service, "logout", logout)

    response = client.post("/auth/logout", headers={"Authorization": "Bearer abc"})

    assert response.status_code == 204
    logout.assert_awaited_once_with("token-teste")


def test_login_rejeita_payload_invalido(client):
    assert client.post("/auth/login", json={"email": "x"}).status_code == 422
