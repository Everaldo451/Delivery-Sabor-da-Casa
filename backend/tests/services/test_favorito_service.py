from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.entities.favorito import Favorito
from app.services.favorito_service import FavoritoService


def test_adicionar_favorito():
    repository = Mock()
    favorito = Favorito(user_id="u-1", prato_id="p-1", criado_em="2026-01-01T00:00:00Z")
    repository.adicionar.return_value = favorito

    resultado = FavoritoService(repository).adicionar("u-1", "p-1")

    assert resultado == favorito
    repository.adicionar.assert_called_once_with("u-1", "p-1")


def test_adicionar_prato_inexistente_retorna_404():
    repository = Mock()
    repository.adicionar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        FavoritoService(repository).adicionar("u-1", "nao-existe")

    assert exc_info.value.status_code == 404


def test_remover_favorito_inexistente_retorna_404():
    repository = Mock()
    repository.remover.return_value = False

    with pytest.raises(HTTPException) as exc_info:
        FavoritoService(repository).remover("u-1", "p-1")

    assert exc_info.value.status_code == 404
