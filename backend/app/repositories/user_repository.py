from sqlalchemy import select
from sqlmodel import Session

from app.database.postgresql import engine
from app.database.postgresql.models.user import UserModel
from app.entities.usuario import Usuario


class UserRepository:
    def buscar_por_email(self, email: str) -> Usuario | None:
        with Session(engine) as session:
            statement = select(UserModel).where(UserModel.email == email)
            user_model = session.exec(statement).first()
            return self._para_entidade(user_model) if user_model is not None else None

    def buscar_por_id(self, user_id: str) -> Usuario | None:
        with Session(engine) as session:
            user_model = session.get(UserModel, user_id)
            return self._para_entidade(user_model) if user_model is not None else None

    @staticmethod
    def _para_entidade(user_model: UserModel) -> Usuario:
        return Usuario(
            id=user_model.id,
            email=user_model.email,
            senha_hash=user_model.senha_hash,
            is_admin=user_model.is_admin,
        )
