from unittest.mock import AsyncMock

from app.routers import auth
from app.schemas.auth import LoginRequest, TokenResponse


def test_login_retorna_token(client, monkeypatch):
    monkeypatch.setattr(
        auth.auth_service,
        "login",
        lambda dados: TokenResponse(
            access_token="jwt-teste",
            refresh_token="refresh-teste",
            expires_in=1800,
            refresh_expires_in=604800,
        ),
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
    logout.assert_awaited_once_with("token-teste", None)


def test_refresh_troca_refresh_token_por_novos_tokens(client, monkeypatch):
    monkeypatch.setattr(
        auth.auth_service,
        "refresh",
        AsyncMock(
            return_value=TokenResponse(
                access_token="novo-access",
                refresh_token="novo-refresh",
                expires_in=1800,
                refresh_expires_in=604800,
            )
        ),
    )

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "refresh-antigo"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "novo-access"
    assert response.json()["refresh_token"] == "novo-refresh"
    auth.auth_service.refresh.assert_awaited_once_with("refresh-antigo")


def test_refresh_rejeita_payload_invalido(client):
    assert client.post("/auth/refresh", json={}).status_code == 422


def test_logout_passa_refresh_token_para_revogacao(client, monkeypatch):
    logout = AsyncMock()
    monkeypatch.setattr(auth.auth_service, "logout", logout)

    response = client.post(
        "/auth/logout",
        headers={"Authorization": "Bearer access-teste"},
        json={"refresh_token": "refresh-teste"},
    )

    assert response.status_code == 204
    logout.assert_awaited_once_with("token-teste", "refresh-teste")


def test_login_rejeita_payload_invalido(client):
    assert client.post("/auth/login", json={"email": "x"}).status_code == 422
