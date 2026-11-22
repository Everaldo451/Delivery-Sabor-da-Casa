from pydantic import BaseModel, Field

from app.entities.carrinho import ItemCarrinho


class ItemCarrinhoIn(BaseModel):
    prato_id: str = Field(min_length=1)
    quantidade: int = Field(ge=1, le=50)
    observacao: str | None = Field(default=None, max_length=200)


class AtualizarItemCarrinho(BaseModel):
    quantidade: int = Field(ge=1, le=50)
    observacao: str | None = Field(default=None, max_length=200)


class AtualizarCarrinho(BaseModel):
    itens: list[ItemCarrinhoIn] = Field(default_factory=list)


class CarrinhoOut(BaseModel):
    user_id: str
    itens: list[ItemCarrinho]
