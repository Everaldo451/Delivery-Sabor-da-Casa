from pydantic import BaseModel


class Usuario(BaseModel):
    id: str
    is_admin: bool = False
