from types import SimpleNamespace

from app.entities.usuario import Usuario
from app.repositories.user_repository import UserRepository


def test_converte_model_de_usuario_para_entidade():
    model = SimpleNamespace(
        id="u-1", nome="Cliente", email="cliente@example.com",
        senha_hash="hash", is_admin=False,
    )

    usuario = UserRepository._para_entidade(model)

    assert usuario == Usuario(
        id="u-1", nome="Cliente", email="cliente@example.com",
        senha_hash="hash", is_admin=False,
    )
