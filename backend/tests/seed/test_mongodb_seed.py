import json
from unittest.mock import AsyncMock, Mock

import pytest

from seed.mongodb import seed as mongo_seed


def test_carregar_zonas_le_as_sete_zonas_geojson():
    zonas = mongo_seed.carregar_zonas()

    assert len(zonas) == 7
    assert len({zona.nome for zona in zonas}) == 7
    assert all(zona.area.poligonos for zona in zonas)
    assert all(zona.valor >= 0 for zona in zonas)


@pytest.mark.parametrize(
    ("dados", "mensagem"),
    [
        ({"type": "Feature"}, "FeatureCollection"),
        ({"type": "FeatureCollection", "features": []}, "exatamente 7 zonas"),
        (
            {
                "type": "FeatureCollection",
                "features": [None] * 7,
            },
            "Feature invalida na posicao 1",
        ),
        (
            {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "properties": {}, "geometry": {}}
                ]
                * 7,
            },
            "Nome ou taxa ausente na zona da posicao 1",
        ),
    ],
)
def test_carregar_zonas_rejeita_geojson_invalido(tmp_path, monkeypatch, dados, mensagem):
    arquivo = tmp_path / "zonas.json"
    arquivo.write_text(json.dumps(dados), encoding="utf-8")
    monkeypatch.setattr(mongo_seed, "ARQUIVO_ZONAS", arquivo)

    with pytest.raises(ValueError, match=mensagem):
        mongo_seed.carregar_zonas()


async def test_seed_cria_indice_e_atualiza_ou_insere_todas_as_zonas(monkeypatch):
    zonas = mongo_seed.carregar_zonas()
    repository = Mock()
    repository.criar_indice_geografico = AsyncMock()
    repository.atualizar_ou_inserir = AsyncMock()
    monkeypatch.setattr(mongo_seed, "carregar_zonas", lambda: zonas)
    monkeypatch.setattr(mongo_seed, "ZonaEntregaRepository", lambda: repository)

    quantidade = await mongo_seed.seed_zonas()

    assert quantidade == 7
    repository.criar_indice_geografico.assert_awaited_once_with()
    assert repository.atualizar_ou_inserir.await_count == 7
    assert [
        chamada.args[0].nome
        for chamada in repository.atualizar_ou_inserir.await_args_list
    ] == [zona.nome for zona in zonas]
