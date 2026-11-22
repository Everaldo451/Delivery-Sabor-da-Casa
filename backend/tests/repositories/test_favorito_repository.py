from datetime import datetime, timezone
from types import SimpleNamespace

from app.repositories.favorito_repository import FavoritoRepository


def test_converte_favorito_model_para_entidade():
    criado_em = datetime.now(timezone.utc)
    modelo = SimpleNamespace(user_id="u-1", prato_id="p-1", criado_em=criado_em)

    favorito = FavoritoRepository._para_entidade(modelo)

    assert favorito.user_id == "u-1"
    assert favorito.prato_id == "p-1"
    assert favorito.criado_em == criado_em
