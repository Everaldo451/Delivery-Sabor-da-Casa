from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

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
    cupom_codigo: str | None = Field(default=None, min_length=3, max_length=30)
    pontos_resgatados: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def exigir_cep(self):
        if not self.endereco_entrega.cep:
            raise ValueError("CEP do endereco de entrega obrigatorio")
        return self

    @field_validator("cupom_codigo")
    @classmethod
    def normalizar_codigo_cupom(cls, codigo: str | None) -> str | None:
        return codigo.strip().upper() if codigo is not None else None


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
    cupom_codigo: str | None = None
    pontos_resgatados: int = 0
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
