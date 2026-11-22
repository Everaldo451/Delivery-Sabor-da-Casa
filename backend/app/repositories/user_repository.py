from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.postgresql import create_session
from app.database.postgresql.models.user import UserModel
from app.entities.usuario import Usuario


class EmailJaCadastradoError(Exception):
    pass


class UserRepository:
    def buscar_por_email(self, email: str) -> Usuario | None:
        with create_session() as session:
            statement = select(UserModel).where(UserModel.email == email)
            user_model = session.exec(statement).first()
            return self._para_entidade(user_model) if user_model is not None else None

    def buscar_por_id(self, user_id: str) -> Usuario | None:
        with create_session() as session:
            user_model = session.get(UserModel, user_id)
            return self._para_entidade(user_model) if user_model is not None else None

    def inserir(self, usuario: Usuario) -> Usuario:
        user_model = UserModel(
            id=usuario.id,
            nome=usuario.nome,
            email=usuario.email,
            senha_hash=usuario.senha_hash,
            is_admin=usuario.is_admin,
        )
        with create_session() as session:
            existing_user = session.exec(
                select(UserModel).where(UserModel.email == usuario.email)
            ).first()
            if existing_user is not None:
                raise EmailJaCadastradoError(usuario.email)

            session.add(user_model)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                existing_user = session.exec(
                    select(UserModel).where(UserModel.email == usuario.email)
                ).first()
                if existing_user is not None:
                    raise EmailJaCadastradoError(usuario.email) from exc
                raise
            session.refresh(user_model)
            return self._para_entidade(user_model)

    @staticmethod
    def _para_entidade(user_model: UserModel) -> Usuario:
        return Usuario(
            id=user_model.id,
            nome=user_model.nome,
            email=user_model.email,
            senha_hash=user_model.senha_hash,
            is_admin=user_model.is_admin,
        )
