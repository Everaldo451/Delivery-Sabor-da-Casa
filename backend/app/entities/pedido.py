from datetime import datetime
from enum import Enum
from re import fullmatch

from pydantic import BaseModel, Field, field_validator

from app.types.geografia import CoordenadaGeografica


class StatusPedido(str, Enum):
    aguardando_pagamento = "aguardando_pagamento"
    recebido = "recebido"
    em_preparo = "em_preparo"
    saiu_para_entrega = "saiu_para_entrega"
    entregue = "entregue"
    cancelado = "cancelado"


class FormaPagamento(str, Enum):
    pix = "pix"
    cartao = "cartao"
    dinheiro = "dinheiro"


class EnderecoEntrega(BaseModel):
    rua: str
    numero: str
    bairro: str
    cep: str | None = None
    complemento: str | None = None
    localizacao: CoordenadaGeografica | None = None

    @field_validator("cep")
    @classmethod
    def normalizar_cep(cls, cep: str | None) -> str | None:
        if cep is None:
            return None
        cep = cep.strip().replace("-", "")
        if not fullmatch(r"\d{8}", cep):
            raise ValueError("O CEP deve conter exatamente 8 digitos")
        return cep


class ItemPedido(BaseModel):
    prato_id: str
    nome: str
    preco_unitario: float
    quantidade: int = Field(ge=1, le=50)
    observacao: str | None = Field(default=None, max_length=200)


class Pedido(BaseModel):
    id: str | None = None
    user_id: str
    cupom_codigo: str | None = None
    pontos_resgatados: int = Field(default=0, ge=0)
    itens: list[ItemPedido] = Field(min_length=1)
    subtotal: float
    desconto: float
    taxa_entrega: float
    total: float
    endereco_entrega: EnderecoEntrega
    forma_pagamento: FormaPagamento
    status: StatusPedido
    criado_em: datetime
    atualizado_em: datetime
