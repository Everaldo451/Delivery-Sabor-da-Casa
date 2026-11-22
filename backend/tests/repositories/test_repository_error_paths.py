from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.entities.cupom import TipoDescontoCupom
from app.repositories.cardapio_repository import (
    CardapioRepository,
    CategoriaEmUsoError,
    CategoriaJaExisteError,
)
from app.repositories.cupom_repository import (
    CupomRepository,
    UsoCupomIndisponivelError,
)
from app.repositories.favorito_repository import FavoritoRepository
from app.repositories.fidelidade_repository import (
    FidelidadeRepository,
    SaldoPontosInsuficienteError,
)
from app.repositories.user_repository import EmailJaCadastradoError, UserRepository


def _integrity_error():
    return IntegrityError("insert", {}, Exception("unique constraint"))


def _patch_session(monkeypatch, module_name, session):
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(f"app.repositories.{module_name}.create_session", lambda: session)


@pytest.mark.parametrize(
    "operation,expected_error",
    [
        ("insert", CategoriaJaExisteError),
        ("update", CategoriaJaExisteError),
        ("remove", CategoriaEmUsoError),
    ],
)
def test_cardapio_converte_integrity_error_em_erro_de_dominio(
    monkeypatch, operation, expected_error
):
    session = Mock()
    _patch_session(monkeypatch, "cardapio_repository", session)
    session.exec.return_value.first.return_value = None
    session.exec.return_value.one.return_value = 0
    session.get.return_value = SimpleNamespace(id=3, nome="Antiga")
    session.commit.side_effect = _integrity_error()
    repository = CardapioRepository()

    with pytest.raises(expected_error):
        if operation == "insert":
            repository.inserir_categoria("Nova")
        elif operation == "update":
            repository.atualizar_categoria(3, "Nova")
        else:
            repository.remover_categoria(3)

    session.rollback.assert_called_once()


def test_cardapio_buscar_imagem_distingue_prato_inexistente(monkeypatch):
    session = Mock()
    _patch_session(monkeypatch, "cardapio_repository", session)
    session.exec.return_value.first.return_value = None

    assert CardapioRepository().buscar_imagem("inexistente") is None


def test_cupom_atualizacao_converte_integrity_error(monkeypatch):
    session = Mock()
    _patch_session(monkeypatch, "cupom_repository", session)
    session.get.return_value = SimpleNamespace()
    session.commit.side_effect = _integrity_error()
    cupom = SimpleNamespace(
        id=8,
        codigo="DUPLICADO",
        descricao="Teste",
        tipo=TipoDescontoCupom.percentual,
        valor=10,
        subtotal_minimo=0,
        desconto_maximo=None,
        valido_de=None,
        valido_ate=None,
        ativo=True,
        limite_usos=None,
        limite_por_usuario=1,
        somente_novos_clientes=False,
    )

    with pytest.raises(Exception) as exc_info:
        CupomRepository().atualizar(cupom)

    from app.repositories.cupom_repository import CodigoCupomDuplicadoError

    assert isinstance(exc_info.value, CodigoCupomDuplicadoError)
    session.rollback.assert_called_once()


@pytest.mark.parametrize("cupom", [None, SimpleNamespace(ativo=False)])
def test_cupom_disponibilidade_recusa_inexistente_ou_inativo(monkeypatch, cupom):
    session = Mock()
    _patch_session(monkeypatch, "cupom_repository", session)
    session.get.return_value = cupom

    with pytest.raises(UsoCupomIndisponivelError):
        CupomRepository().validar_disponibilidade(1, "user")


def test_cupom_disponibilidade_recusa_limite_total(monkeypatch):
    session = Mock()
    _patch_session(monkeypatch, "cupom_repository", session)
    session.get.return_value = SimpleNamespace(ativo=True, limite_usos=1, limite_por_usuario=None, somente_novos_clientes=False)
    session.exec.return_value.one.return_value = 1

    with pytest.raises(UsoCupomIndisponivelError, match="Limite total"):
        CupomRepository().validar_disponibilidade(1, "user")


def test_cupom_sem_limites_ignora_contadores(monkeypatch):
    session = Mock()
    session.get.return_value = SimpleNamespace(
        ativo=True,
        limite_usos=None,
        limite_por_usuario=None,
        somente_novos_clientes=False,
    )

    CupomRepository._validar_limites(session, 1, "user")

    session.exec.assert_not_called()


def test_favorito_recupera_favorito_criado_concorrente(monkeypatch):
    session = Mock()
    _patch_session(monkeypatch, "favorito_repository", session)
    recovered = SimpleNamespace(user_id="u-1", prato_id="p-1", criado_em=datetime.now(timezone.utc))
    session.get.side_effect = [SimpleNamespace(id="p-1"), None, recovered]
    session.commit.side_effect = _integrity_error()

    result = FavoritoRepository().adicionar("u-1", "p-1")

    assert result.user_id == "u-1"
    session.rollback.assert_called_once()
    session.refresh.assert_called_once_with(recovered)


def test_favorito_repropaga_integrity_error_sem_favorito_concorrente(monkeypatch):
    session = Mock()
    _patch_session(monkeypatch, "favorito_repository", session)
    session.get.side_effect = [SimpleNamespace(id="p-1"), None, None]
    session.commit.side_effect = _integrity_error()

    with pytest.raises(IntegrityError):
        FavoritoRepository().adicionar("u-1", "p-1")
    session.rollback.assert_called_once()


def _result(first=None, one=None):
    result = Mock()
    result.first.return_value = first
    result.one.return_value = one
    return result


def test_resgate_converte_integrity_error(monkeypatch):
    session = Mock()
    _patch_session(monkeypatch, "fidelidade_repository", session)
    session.exec.side_effect = [
        _result(first="u-1"),
        _result(first=None),
        _result(one=50),
    ]
    session.commit.side_effect = _integrity_error()

    with pytest.raises(SaldoPontosInsuficienteError):
        FidelidadeRepository().resgatar("u-1", "pedido-1", 10)
    session.rollback.assert_called_once()


def test_credito_duplicado_concorrente_reverte_e_retorna_saldo(monkeypatch):
    session = Mock()
    _patch_session(monkeypatch, "fidelidade_repository", session)
    session.exec.side_effect = [
        _result(first="u-1"),
        _result(first=None),
        _result(one=20),
    ]
    session.commit.side_effect = _integrity_error()

    assert FidelidadeRepository().creditar_por_pedido("u-1", "pedido-1", 20) == 20
    session.rollback.assert_called_once()


@pytest.mark.parametrize("raced_user", [True, False])
def test_user_repository_trata_integrity_error_de_cadastro(monkeypatch, raced_user):
    session = Mock()
    _patch_session(monkeypatch, "user_repository", session)
    user = SimpleNamespace(id="u-1", nome="Teste", email="u-1@example.com", senha_hash="hash", is_admin=False)
    session.exec.side_effect = [
        _result(first=None),
        _result(first=user if raced_user else None),
    ]
    session.commit.side_effect = _integrity_error()
    entity = UserRepository()
    from app.entities.usuario import Usuario

    usuario = Usuario(id="u-1", nome="Teste", email="u-1@example.com", senha_hash="hash")
    if raced_user:
        with pytest.raises(EmailJaCadastradoError):
            entity.inserir(usuario)
    else:
        with pytest.raises(IntegrityError):
            entity.inserir(usuario)
    session.rollback.assert_called_once()
