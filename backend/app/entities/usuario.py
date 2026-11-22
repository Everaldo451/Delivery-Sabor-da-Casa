from pydantic import BaseModel, Field


class Usuario(BaseModel):
    id: str
    email: str
    senha_hash: str = Field(exclude=True, repr=False)
    is_admin: bool = False
    nome: str = ""
