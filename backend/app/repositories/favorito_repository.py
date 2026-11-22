from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.postgresql import create_session
from app.database.postgresql.models.cardapio import PratoModel
from app.database.postgresql.models.favorito import FavoritoModel
from app.entities.favorito import Favorito


class FavoritoRepository:
    def listar(self, user_id: str) -> list[Favorito]:
        with create_session() as session:
            favoritos = session.exec(
                select(FavoritoModel)
                .where(FavoritoModel.user_id == user_id)
                .order_by(FavoritoModel.criado_em.desc())
            ).all()
            return [self._para_entidade(favorito) for favorito in favoritos]

    def adicionar(self, user_id: str, prato_id: str) -> Favorito | None:
        with create_session() as session:
            prato = session.get(PratoModel, prato_id)
            if prato is None:
                return None

            favorito = session.get(FavoritoModel, (user_id, prato_id))
            if favorito is None:
                favorito = FavoritoModel(user_id=user_id, prato_id=prato_id)
                session.add(favorito)
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    favorito = session.get(FavoritoModel, (user_id, prato_id))
                    if favorito is None:
                        raise
                session.refresh(favorito)
            return self._para_entidade(favorito)

    def remover(self, user_id: str, prato_id: str) -> bool:
        with create_session() as session:
            favorito = session.get(FavoritoModel, (user_id, prato_id))
            if favorito is None:
                return False
            session.delete(favorito)
            session.commit()
            return True

    @staticmethod
    def _para_entidade(favorito: FavoritoModel) -> Favorito:
        return Favorito(
            user_id=favorito.user_id,
            prato_id=favorito.prato_id,
            criado_em=favorito.criado_em,
        )
