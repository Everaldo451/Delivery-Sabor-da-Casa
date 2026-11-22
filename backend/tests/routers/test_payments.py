from unittest.mock import Mock

from app.routers import payments


def test_listar_pagamentos_do_usuario(client):
    service = Mock()
    service.listar.return_value = []
    client.app.dependency_overrides[payments.get_payment_service] = lambda: service

    response = client.get("/payments")

    assert response.status_code == 200
    assert response.json() == []
    service.listar.assert_called_once()


def test_checkout_valida_payload(client):
    assert client.post("/checkout", json={}).status_code == 422
