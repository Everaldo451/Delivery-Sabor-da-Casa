from pydantic import BaseModel, Field


class ItemCarrinho(BaseModel):
    prato_id: str = Field(min_length=1)
    quantidade: int = Field(ge=1, le=50)
    observacao: str | None = Field(default=None, max_length=200)


class Carrinho(BaseModel):
    user_id: str
    itens: list[ItemCarrinho] = Field(default_factory=list)
