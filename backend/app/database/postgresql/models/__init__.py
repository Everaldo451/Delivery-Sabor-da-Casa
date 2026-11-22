from app.database.postgresql.models.cardapio import CategoriaModel, PratoModel
from app.database.postgresql.models.cupom import CupomModel
from app.database.postgresql.models.cupom_uso import CupomUsoModel
from app.database.postgresql.models.favorito import FavoritoModel
from app.database.postgresql.models.fidelidade import TransacaoFidelidadeModel
from app.database.postgresql.models.payment import PaymentModel
from app.database.postgresql.models.user import UserModel

__all__ = [
    "CategoriaModel",
    "CupomModel",
    "CupomUsoModel",
    "FavoritoModel",
    "PaymentModel",
    "PratoModel",
    "TransacaoFidelidadeModel",
    "UserModel",
]
