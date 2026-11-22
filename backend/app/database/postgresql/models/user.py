from uuid import uuid4

from sqlmodel import Field, SQLModel


class UserModel(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    nome: str = Field(max_length=120)
    email: str = Field(index=True, unique=True, max_length=254)
    senha_hash: str = Field(max_length=255)
    is_admin: bool = Field(default=False)
