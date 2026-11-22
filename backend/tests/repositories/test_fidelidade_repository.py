from datetime import datetime, timezone
from types import SimpleNamespace

from app.repositories.fidelidade_repository import FidelidadeRepository


def test_converte_transacao_fidelidade_model_para_entidade():
    criado_em = datetime.now(timezone.utc)
    modelo = SimpleNamespace(
        id=3,
        user_id="u-1",
        pedido_id="pedido-1",
        pontos=-100,
        tipo="resgate_pedido",
        criado_em=criado_em,
    )

    transacao = FidelidadeRepository._para_entidade(modelo)

    assert transacao.model_dump() == {
        "id": 3,
        "user_id": "u-1",
        "pedido_id": "pedido-1",
        "pontos": -100,
        "tipo": "resgate_pedido",
        "criado_em": criado_em,
    }
