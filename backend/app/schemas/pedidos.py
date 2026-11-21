from datetime import datetime

from pydantic import BaseModel, Field

from app.entities.pedido import EnderecoEntrega, FormaPagamento, StatusPedido


# ---------- entrada ----------
class ItemPedidoIn(BaseModel):
    prato_id: str
    quantidade: int = Field(ge=1, le=50)
    observacao: str | None = Field(default=None, max_length=200)


class PedidoCreate(BaseModel):
    itens: list[ItemPedidoIn] = Field(min_length=1)
    endereco_entrega: EnderecoEntrega
    forma_pagamento: FormaPagamento


class AtualizarStatus(BaseModel):
    status: StatusPedido


# ---------- saida ----------
class ItemPedidoOut(BaseModel):
    prato_id: str
    nome: str
    preco_unitario: float
    quantidade: int
    observacao: str | None = None


class PedidoOut(BaseModel):
    id: str
    user_id: str
    itens: list[ItemPedidoOut]
    subtotal: float
    desconto: float
    taxa_entrega: float
    total: float
    endereco_entrega: EnderecoEntrega
    forma_pagamento: FormaPagamento
    status: StatusPedido
    criado_em: datetime
    atualizado_em: datetime


class ItemRepetir(BaseModel):
    """Item de um pedido antigo, com o preco ATUAL do cardapio, pronto pro carrinho."""

    prato_id: str
    nome: str
    preco_atual: float
    quantidade: int
    observacao: str | None = None
    disponivel: bool
