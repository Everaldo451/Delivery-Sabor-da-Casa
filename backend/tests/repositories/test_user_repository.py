from uuid import uuid4
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


def test_inserir_e_buscar_usuario_no_banco_sqlite(sqlite_postgres):
    repository = UserRepository()
    email = f"{uuid4()}@example.com"
    usuario = Usuario(
        id=str(uuid4()),
        nome="Usuario de teste",
        email=email,
        senha_hash="hash-teste",
        is_admin=True,
    )

    assert repository.inserir(usuario) == usuario
    assert repository.buscar_por_email(email) == usuario
    assert repository.buscar_por_id(usuario.id) == usuario
    assert repository.buscar_por_email("inexistente@example.com") is None
    assert repository.buscar_por_id("inexistente") is None
