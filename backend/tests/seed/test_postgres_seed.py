import bcrypt
import pytest
from sqlalchemy import func
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy.pool import StaticPool

from app.database.postgresql.models.cardapio import CategoriaModel, PratoModel
from app.database.postgresql.models.user import UserModel
from seed.postgres.seed import aplicar_seed, carregar_dados


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()


def test_arquivos_seed_contem_usuarios_categorias_e_quarenta_pratos():
    dados = carregar_dados()

    assert len(dados.usuarios) == 2
    assert sum(usuario.is_admin for usuario in dados.usuarios) == 1
    assert {categoria.nome for categoria in dados.categorias} == {
        "Entrada",
        "Prato Principal",
        "Sobremesa",
        "Bebidas",
    }
    assert len(dados.pratos) == 40
    assert {prato.categoria for prato in dados.pratos} == {
        "Entrada",
        "Prato Principal",
        "Sobremesa",
        "Bebidas",
    }


def test_aplica_seed_com_dois_usuarios_e_quarenta_pratos(session):
    dados = carregar_dados()
    senhas = {
        "SEED_ADMIN_PASSWORD": "senha-admin-teste",
        "SEED_USER_PASSWORD": "senha-cliente-teste",
    }

    resultado = aplicar_seed(session, dados, senhas)

    assert resultado == {"usuarios": 2, "categorias": 4, "pratos": 40}
    admin = session.get(UserModel, "seed-admin")
    cliente = session.get(UserModel, "seed-cliente")
    assert admin is not None and admin.is_admin is True
    assert cliente is not None and cliente.is_admin is False
    assert bcrypt.checkpw(
        b"senha-admin-teste", admin.senha_hash.encode("ascii")
    )
    assert bcrypt.checkpw(
        b"senha-cliente-teste", cliente.senha_hash.encode("ascii")
    )
    assert session.scalar(select(func.count()).select_from(CategoriaModel)) == 4
    assert session.scalar(select(func.count()).select_from(PratoModel)) == 40
    assert session.get(PratoModel, "seed-prato-001").categoria_id is not None


def test_aplicar_seed_e_idempotente(session):
    dados = carregar_dados()
    senhas = {
        "SEED_ADMIN_PASSWORD": "senha-admin-teste",
        "SEED_USER_PASSWORD": "senha-cliente-teste",
    }

    aplicar_seed(session, dados, senhas)
    aplicar_seed(session, dados, senhas)

    assert session.scalar(select(func.count()).select_from(UserModel)) == 2
    assert session.scalar(select(func.count()).select_from(CategoriaModel)) == 4
    assert session.scalar(select(func.count()).select_from(PratoModel)) == 40


def test_senhas_ausentes_falham_sem_inserir_dados(session):
    with pytest.raises(ValueError, match="SEED_ADMIN_PASSWORD"):
        aplicar_seed(session, carregar_dados(), {})

    assert session.scalar(select(func.count()).select_from(UserModel)) == 0
