from datetime import date
from decimal import Decimal

from app.database.postgresql.models.cupom import CupomModel
from app.entities.cupom import Cupom, TipoDescontoCupom
from app.repositories.cupom_repository import CupomRepository


def test_converte_cupom_entre_modelo_e_entidade():
    cupom = Cupom(
        id=1,
        codigo="BEMVINDO",
        descricao="Desconto inicial",
        tipo=TipoDescontoCupom.percentual,
        valor=Decimal("10.00"),
        subtotal_minimo=Decimal("20.00"),
        desconto_maximo=Decimal("15.00"),
        valido_de=date(2026, 1, 1),
        valido_ate=date(2026, 12, 31),
        ativo=True,
        limite_usos=100,
        limite_por_usuario=1,
        somente_novos_clientes=True,
    )

    repository = CupomRepository()
    modelo = repository._para_modelo(cupom)
    entidade = repository._para_entidade(modelo)

    assert isinstance(modelo, CupomModel)
    assert modelo.tipo == "percentual"
    assert entidade == cupom
