from datetime import date
from decimal import Decimal
from re import fullmatch

from pydantic import BaseModel, Field, field_validator, model_validator

from app.entities.cupom import TipoDescontoCupom


class CupomCreate(BaseModel):
    codigo: str = Field(min_length=3, max_length=30)
    descricao: str = Field(min_length=1, max_length=250)
    tipo: TipoDescontoCupom
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    subtotal_minimo: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)
    desconto_maximo: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    limite_usos: int | None = Field(default=None, gt=0)
    limite_por_usuario: int | None = Field(default=1, gt=0)
    somente_novos_clientes: bool = False
    valido_de: date | None = None
    valido_ate: date | None = None
    ativo: bool = True

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo(cls, codigo: str) -> str:
        codigo = codigo.strip().upper()
        if not fullmatch(r"[A-Z0-9_-]{3,30}", codigo):
            raise ValueError("O código deve conter apenas letras, números, _ ou -")
        return codigo

    @model_validator(mode="after")
    def validar_configuracao_desconto(self):
        if self.valido_de and self.valido_ate and self.valido_ate < self.valido_de:
            raise ValueError("A data final deve ser posterior à data inicial")
        if self.tipo == TipoDescontoCupom.percentual and self.valor > 100:
            raise ValueError("O desconto percentual não pode passar de 100")
        if self.tipo == TipoDescontoCupom.valor_fixo and self.desconto_maximo is not None:
            raise ValueError("Desconto máximo só se aplica a cupons percentuais")
        return self


class CupomAtualizar(CupomCreate):
    pass


class CupomOut(CupomCreate):
    id: int


class CupomValidarIn(BaseModel):
    codigo: str = Field(min_length=3, max_length=30)
    subtotal: Decimal = Field(ge=0, max_digits=10, decimal_places=2)

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo(cls, codigo: str) -> str:
        return CupomCreate.normalizar_codigo(codigo)


class CupomDescontoOut(BaseModel):
    codigo: str
    desconto: Decimal
