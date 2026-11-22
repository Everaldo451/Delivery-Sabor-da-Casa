from decimal import Decimal
from unittest.mock import Mock

from app.routers import cardapio
from app.schemas.cardapio import CategoriaOut, ImagemPratoOut, PratoOut


def test_listar_categorias(client):
    service = Mock()
    service.listar_categorias.return_value = [CategoriaOut(id=1, nome="Pratos")]
    client.app.dependency_overrides[cardapio.get_cardapio_service] = lambda: service

    response = client.get("/cardapio/categorias")

    assert response.status_code == 200
    assert response.json() == [{"id": 1, "nome": "Pratos"}]


def test_criar_prato_exige_admin_e_retorna_prato(client):
    service = Mock()
    service.criar_prato.return_value = PratoOut(
        id="p-1", nome="Massa", descricao="Descrição", preco=Decimal("20.00"),
        categoria="Pratos", imagem=ImagemPratoOut(url="/cardapio/p-1/imagem", content_type="image/png"),
        disponivel=True,
    )
    client.app.dependency_overrides[cardapio.get_cardapio_service] = lambda: service

    response = client.post("/cardapio", json={
        "nome": "Massa", "descricao": "Descrição", "preco": "20.00",
        "categoria": "Pratos", "disponivel": True,
    })

    assert response.status_code == 201
    assert response.json()["id"] == "p-1"
    service.criar_prato.assert_called_once()


def test_obter_imagem_preserva_bytes_e_content_type(client):
    service = Mock()
    service.buscar_imagem.return_value = Mock(imagem=b"\x89PNG", content_type="image/png")
    client.app.dependency_overrides[cardapio.get_cardapio_service] = lambda: service

    response = client.get("/cardapio/p-1/imagem")

    assert response.status_code == 200
    assert response.content == b"\x89PNG"
    assert response.headers["content-type"] == "image/png"


def test_categoria_invalida_retorna_422(client):
    assert client.post("/cardapio/categorias", json={"nome": "  "}).status_code == 422
