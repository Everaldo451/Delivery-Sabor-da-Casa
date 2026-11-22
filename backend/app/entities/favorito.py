from datetime import datetime

from pydantic import BaseModel


class Favorito(BaseModel):
    user_id: str
    prato_id: str
    criado_em: datetime
