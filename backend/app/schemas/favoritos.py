from datetime import datetime

from pydantic import BaseModel


class FavoritoOut(BaseModel):
    prato_id: str
    criado_em: datetime
