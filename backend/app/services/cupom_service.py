from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException

from app.entities.cupom import Cupom, TipoDescontoCupom
from app.repositories.cupom_repository import (
    CodigoCupomDuplicadoError,
    CupomRepository,
    UsoCupomIndisponivelError,
)
from app.schemas.cupons import CupomAtualizar, CupomCreate, CupomOut

CENTAVO = Decimal("0.01")


class CupomService:
    def __init__(self, repository: CupomRepository | None = None) -> None:
        self._repository = repository or CupomRepository()

    def listar(self) -> list[CupomOut]:
        hoje = datetime.now(timezone.utc).date()
        cupons = self._repository.listar()
        return [
            self._para_saida(cupom)
            for cupom in cupons
            if cupom.ativo
            and (cupom.valido_de is None or cupom.valido_de <= hoje)
            and (cupom.valido_ate is None or cupom.valido_ate >= hoje)
        ]

    def listar_todos(self) -> list[CupomOut]:
        return [self._para_saida(cupom) for cupom in self._repository.listar()]

    def criar(self, dados: CupomCreate) -> CupomOut:
        try:
            cupom = self._repository.inserir(Cupom(**dados.model_dump()))
        except CodigoCupomDuplicadoError as exc:
            raise HTTPException(409, "Codigo de cupom ja cadastrado") from exc
        return self._para_saida(cupom)

    def atualizar(self, cupom_id: int, dados: CupomAtualizar) -> CupomOut:
        try:
            cupom = self._repository.atualizar(
                Cupom(id=cupom_id, **dados.model_dump())
            )
        except CodigoCupomDuplicadoError as exc:
            raise HTTPException(409, "Codigo de cupom ja cadastrado") from exc
        if cupom is None:
            raise HTTPException(404, "Cupom nao encontrado")
        return self._para_saida(cupom)

    def remover(self, cupom_id: int) -> None:
        if not self._repository.remover(cupom_id):
            raise HTTPException(404, "Cupom nao encontrado")

    def calcular_desconto(
        self, codigo: str, subtotal: Decimal, user_id: str
    ) -> Decimal:
        cupom = self._repository.buscar_por_codigo(codigo.strip().upper())
        if cupom is None:
            raise HTTPException(422, "Cupom invalido")
        self._validar_uso(cupom, subtotal)
        try:
            self._repository.validar_disponibilidade(cupom.id, user_id)
        except UsoCupomIndisponivelError as exc:
            raise HTTPException(422, str(exc)) from exc

        if cupom.tipo == TipoDescontoCupom.percentual:
            desconto = (subtotal * cupom.valor / Decimal("100")).quantize(
                CENTAVO,
                rounding=ROUND_HALF_UP,
            )
            if cupom.desconto_maximo is not None:
                desconto = min(desconto, cupom.desconto_maximo)
        else:
            desconto = cupom.valor
        return min(desconto, subtotal).quantize(CENTAVO, rounding=ROUND_HALF_UP)

    def registrar_uso(
        self, codigo: str, user_id: str, pedido_id: str, subtotal: Decimal
    ) -> None:
        try:
            self._repository.registrar_uso(
                codigo.strip().upper(), user_id, pedido_id, subtotal
            )
        except UsoCupomIndisponivelError as exc:
            raise HTTPException(409, str(exc)) from exc

    def estornar_uso(self, pedido_id: str) -> None:
        self._repository.estornar_uso(pedido_id)

    @staticmethod
    def _validar_uso(cupom: Cupom, subtotal: Decimal) -> None:
        hoje = datetime.now(timezone.utc).date()
        if not cupom.ativo:
            raise HTTPException(422, "Cupom inativo")
        if cupom.valido_de is not None and cupom.valido_de > hoje:
            raise HTTPException(422, "Cupom ainda nao esta valido")
        if cupom.valido_ate is not None and cupom.valido_ate < hoje:
            raise HTTPException(422, "Cupom expirado")
        if subtotal < cupom.subtotal_minimo:
            raise HTTPException(422, "Subtotal minimo do cupom nao atingido")

    @staticmethod
    def _para_saida(cupom: Cupom) -> CupomOut:
        return CupomOut.model_validate(cupom.model_dump())
