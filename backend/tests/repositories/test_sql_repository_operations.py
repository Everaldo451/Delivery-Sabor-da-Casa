from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.entities.cardapio import ImagemPrato, Prato
from app.entities.cupom import Cupom, TipoDescontoCupom
from app.entities.payment import Payment, PaymentStatus
from app.entities.pedido import FormaPagamento
from app.entities.usuario import Usuario
from app.repositories.cardapio_repository import (
    CardapioRepository,
    CategoriaEmUsoError,
    CategoriaJaExisteError,
    CategoriaNaoEncontradaError,
)
from app.repositories.cupom_repository import (
    CodigoCupomDuplicadoError,
    CupomRepository,
    UsoCupomIndisponivelError,
)
from app.repositories.favorito_repository import FavoritoRepository
from app.repositories.fidelidade_repository import (
    FidelidadeRepository,
    SaldoPontosInsuficienteError,
)
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import EmailJaCadastradoError, UserRepository


def make_user(user_id: str | None = None) -> Usuario:
    user_id = user_id or str(uuid4())
    return Usuario(
        id=user_id,
        nome="Cliente Teste",
        email=f"{user_id}@example.com",
        senha_hash="hash-teste",
    )


def make_prato(prato_id: str | None = None, categoria: str = "Pratos") -> Prato:
    return Prato(
        id=prato_id,
        nome="Prato Teste",
        descricao="Descricao de teste",
        preco=Decimal("12.50"),
        categoria=categoria,
    )


def make_cupom(**updates) -> Cupom:
    values = {
        "codigo": f"CUPOM{uuid4().hex[:8].upper()}",
        "descricao": "Cupom de teste",
        "tipo": TipoDescontoCupom.valor_fixo,
        "valor": Decimal("5.00"),
        "subtotal_minimo": Decimal("10.00"),
        "limite_usos": None,
        "limite_por_usuario": None,
        "somente_novos_clientes": False,
        "ativo": True,
    }
    values.update(updates)
    return Cupom(**values)


def test_user_repository_crud_e_email_duplicado(sqlite_postgres):
    repository = UserRepository()
    usuario = make_user()

    assert repository.buscar_por_email(usuario.email) is None
    assert repository.buscar_por_id(usuario.id) is None
    assert repository.inserir(usuario) == usuario
    assert repository.buscar_por_email(usuario.email) == usuario
    assert repository.buscar_por_id(usuario.id) == usuario
    with pytest.raises(EmailJaCadastradoError):
        repository.inserir(usuario)


def test_payment_repository_crud_e_listagem_por_usuario(sqlite_postgres):
    UserRepository().inserir(make_user("payment-user"))
    repository = PaymentRepository()
    now = datetime.now(timezone.utc)
    payment = Payment(
        pedido_id="pedido-payment-1",
        user_id="payment-user",
        amount=Decimal("23.50"),
        method=FormaPagamento.pix,
        status=PaymentStatus.aprovado,
        simulation_result="aprovado",
        created_at=now,
        updated_at=now,
    )

    inserted = repository.inserir(payment)
    assert inserted.id is not None
    assert repository.buscar_por_id(inserted.id) == inserted
    assert repository.buscar_por_id(99999) is None
    assert repository.listar_por_usuario("payment-user") == [inserted]
    assert repository.listar_por_usuario("outro-usuario") == []


def test_favorito_repository_add_list_remove_and_missing_prato(sqlite_postgres):
    users = UserRepository()
    users.inserir(make_user("favorite-user"))
    menu = CardapioRepository()
    menu.inserir_categoria("Pratos")
    menu.inserir_prato(make_prato("favorite-dish"))
    repository = FavoritoRepository()

    assert repository.listar("favorite-user") == []
    assert repository.adicionar("favorite-user", "missing-dish") is None
    favorito = repository.adicionar("favorite-user", "favorite-dish")
    assert favorito is not None
    assert favorito.user_id == "favorite-user"
    assert repository.adicionar("favorite-user", "favorite-dish") == favorito
    assert repository.listar("favorite-user") == [favorito]
    assert repository.remover("favorite-user", "missing-dish") is False
    assert repository.remover("favorite-user", "favorite-dish") is True
    assert repository.listar("favorite-user") == []


def test_fidelidade_repository_credito_resgate_estorno_e_limites(sqlite_postgres):
    UserRepository().inserir(make_user("points-user"))
    repository = FidelidadeRepository()

    assert repository.saldo("points-user") == 0
    assert repository.creditar_por_pedido("points-user", "pedido-1", 100) == 100
    assert repository.creditar_por_pedido("points-user", "pedido-1", 100) == 100
    assert repository.creditar_por_pedido("points-user", "pedido-zero", 0) == 100
    assert repository.resgatar("points-user", "pedido-resgate", 40) == 60
    assert repository.resgatar("points-user", "pedido-resgate", 40) == 60
    with pytest.raises(SaldoPontosInsuficienteError):
        repository.resgatar("points-user", "pedido-resgate", 30)
    with pytest.raises(SaldoPontosInsuficienteError):
        repository.resgatar("points-user", "pedido-demais", 61)

    transacoes = repository.listar_transacoes("points-user")
    assert len(transacoes) == 2
    assert repository.estornar_resgate("points-user", "pedido-sem-resgate") == 60
    assert repository.estornar_resgate("points-user", "pedido-resgate") == 100
    assert repository.estornar_resgate("points-user", "pedido-resgate") == 100
    assert len(repository.listar_transacoes("points-user")) == 3
    with pytest.raises(LookupError):
        repository.resgatar("usuario-inexistente", "pedido-x", 1)


def test_cupom_repository_crud_regras_de_uso_e_estorno(sqlite_postgres):
    repository = CupomRepository()
    cupom = make_cupom(limite_usos=2, limite_por_usuario=1)

    assert repository.listar() == []
    assert repository.buscar_por_codigo(cupom.codigo) is None
    inserted = repository.inserir(cupom)
    assert inserted.id is not None
    assert repository.buscar_por_codigo(cupom.codigo) == inserted
    assert repository.listar() == [inserted]
    assert repository.atualizar(make_cupom()) is None
    assert repository.atualizar(cupom.model_copy(update={"id": 99999})) is None

    updated = inserted.model_copy(update={"descricao": "Atualizado"})
    assert repository.atualizar(updated) == updated
    repository.validar_disponibilidade(inserted.id, "cupom-user")
    repository.registrar_uso(inserted.codigo, "cupom-user", "pedido-cupom-1", Decimal("20"))
    # Registrar de novo o mesmo pedido é idempotente.
    repository.registrar_uso(inserted.codigo, "cupom-user", "pedido-cupom-1", Decimal("20"))
    with pytest.raises(UsoCupomIndisponivelError, match="Limite de uso"):
        repository.registrar_uso(inserted.codigo, "cupom-user", "pedido-cupom-2", Decimal("20"))

    repository.estornar_uso("pedido-cupom-1")
    repository.registrar_uso(inserted.codigo, "cupom-user", "pedido-cupom-2", Decimal("20"))
    repository.estornar_uso("pedido-inexistente")
    assert repository.remover(99999) is False
    assert repository.remover(inserted.id) is True
    assert repository.buscar_por_codigo(inserted.codigo).ativo is False


def test_cupom_recusa_subtotal_validade_novos_clientes_e_duplicidade(sqlite_postgres):
    repository = CupomRepository()
    cupom = repository.inserir(make_cupom(
        codigo="NOVOCLIENTE",
        valido_de=date(2099, 1, 1),
        somente_novos_clientes=True,
    ))
    with pytest.raises(UsoCupomIndisponivelError, match="indisponivel"):
        repository.registrar_uso(cupom.codigo, "user", "pedido-baixo", Decimal("1"))
    with pytest.raises(UsoCupomIndisponivelError, match="indisponivel"):
        repository.registrar_uso(cupom.codigo, "user", "pedido-futuro", Decimal("20"))

    # Cupom ativo e válido, mas o cliente já tem um pagamento aprovado.
    approved_user = make_user("approved-coupon-user")
    UserRepository().inserir(approved_user)
    PaymentRepository().inserir(Payment(
        pedido_id="pedido-pago",
        user_id=approved_user.id,
        amount=Decimal("20"),
        method=FormaPagamento.pix,
        status=PaymentStatus.aprovado,
    ))
    valid = repository.inserir(make_cupom(codigo="SOCLIENTENOVO", somente_novos_clientes=True))
    repository.validar_disponibilidade(valid.id, "new-customer")
    with pytest.raises(UsoCupomIndisponivelError, match="novos clientes"):
        repository.registrar_uso(valid.codigo, approved_user.id, "pedido-novo", Decimal("20"))

    with pytest.raises(CodigoCupomDuplicadoError):
        repository.inserir(make_cupom(codigo="SOCLIENTENOVO"))


def test_cardapio_repository_categorias_pratos_imagens_e_filtros(sqlite_postgres):
    repository = CardapioRepository()
    assert repository.listar_categorias() == []
    categoria = repository.inserir_categoria("  Pratos  ")
    bebidas = repository.inserir_categoria("Bebidas")
    assert categoria.nome == "Pratos"
    assert [item.nome for item in repository.listar_categorias()] == ["Pratos", "Bebidas"]
    with pytest.raises(CategoriaJaExisteError):
        repository.inserir_categoria("Pratos")

    assert repository.atualizar_categoria(999, "Nova") is None
    assert repository.atualizar_categoria(categoria.id, "Pratos") == categoria
    with pytest.raises(CategoriaJaExisteError):
        repository.atualizar_categoria(categoria.id, "Bebidas")
    assert repository.remover_categoria(999) is False

    dish = repository.inserir_prato(make_prato("dish-1"))
    assert dish.categoria == "Pratos"
    assert dish.imagem is None
    assert [item.id for item in repository.listar_pratos()] == ["dish-1"]
    assert [item.id for item in repository.listar_pratos("  PRATOS ")] == ["dish-1"]
    assert repository.listar_pratos("Bebidas") == []
    assert repository.buscar_prato("dish-1") == dish
    assert repository.buscar_prato("missing") is None
    assert repository.buscar_imagem("dish-1") is None

    with pytest.raises(CategoriaEmUsoError):
        repository.remover_categoria(categoria.id)
    with pytest.raises(CategoriaNaoEncontradaError):
        repository.inserir_prato(make_prato("dish-missing-category", "Desconhecida"))

    imagem = ImagemPrato(imagem=b"png-bytes", content_type="image/png")
    assert repository.salvar_imagem("dish-1", imagem) is True
    assert repository.buscar_imagem("dish-1") == imagem
    assert repository.salvar_imagem("missing", imagem) is False
    with pytest.raises(ValueError, match="bytes"):
        repository.salvar_imagem("dish-1", ImagemPrato(content_type="image/png"))
    assert repository.remover_imagem("missing") is False
    assert repository.remover_imagem("dish-1") is True
    assert repository.buscar_imagem("dish-1") is None

    updated = dish.model_copy(update={"nome": "Prato Atualizado", "categoria": "Bebidas"})
    assert repository.atualizar_prato(make_prato()) is None
    assert repository.atualizar_prato(make_prato("missing")) is None
    assert repository.atualizar_prato(updated).categoria == "Bebidas"
    assert repository.remover_prato("missing") is False
    assert repository.remover_prato("dish-1") is True
    assert repository.remover_categoria(categoria.id) is True


def test_cardapio_retorna_prato_com_imagem_e_categoria_atualizada(sqlite_postgres):
    repository = CardapioRepository()
    repository.inserir_categoria("Pratos")
    dish = repository.inserir_prato(make_prato("dish-image"))
    entity_with_image = dish.model_copy(update={
        "imagem": ImagemPrato(content_type="image/webp"),
    })
    # Verifica conversão do modelo quando a coluna de MIME está preenchida.
    model = type("PratoModelStub", (), {
        "id": "dish-image",
        "nome": "Prato Teste",
        "descricao": "Descricao de teste",
        "preco": Decimal("12.50"),
        "categoria": type("CategoriaStub", (), {"nome": "Pratos"})(),
        "imagem_content_type": "image/webp",
        "disponivel": True,
    })()
    assert repository._prato_para_entidade(model) == entity_with_image
