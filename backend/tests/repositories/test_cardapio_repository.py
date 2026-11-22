from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

from app.entities.cardapio import ImagemPrato, Prato
from app.repositories.cardapio_repository import CardapioRepository


def test_converte_model_prato_com_categoria_e_imagem_para_entidade():
    model = SimpleNamespace(
        id="p-1", nome="Prato", descricao="Descrição", preco=Decimal("12.50"),
        categoria=SimpleNamespace(nome="Pratos"), imagem_content_type="image/png",
        disponivel=True,
    )

    prato = CardapioRepository._prato_para_entidade(model)

    assert prato == Prato(
        id="p-1", nome="Prato", descricao="Descrição", preco=Decimal("12.50"),
        categoria="Pratos", imagem=ImagemPrato(content_type="image/png"), disponivel=True,
    )


def test_converte_categoria_model_para_entidade():
    assert CardapioRepository._categoria_para_entidade(
        SimpleNamespace(id=4, nome="Bebidas")
    ).model_dump() == {"id": 4, "nome": "Bebidas"}


def test_buscar_imagem_monta_entidade_com_bytes(monkeypatch):
    session = Mock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    session.exec.return_value.first.return_value = (bytearray(b"png"), "image/png")
    monkeypatch.setattr("app.repositories.cardapio_repository.create_session", lambda: session)

    imagem = CardapioRepository().buscar_imagem("p-1")

    assert imagem == ImagemPrato(imagem=b"png", content_type="image/png")
