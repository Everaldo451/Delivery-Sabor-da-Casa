from decimal import Decimal

from fastapi import HTTPException

from app.entities.fidelidade import SaldoFidelidade
from app.repositories.fidelidade_repository import (
    FidelidadeRepository,
    SaldoPontosInsuficienteError,
)

PONTOS_POR_REAL = 1
VALOR_PONTO = Decimal("0.01")


class FidelidadeService:
    def __init__(self, repository: FidelidadeRepository | None = None) -> None:
        self._repository = repository or FidelidadeRepository()

    def obter_saldo(self, user_id: str) -> SaldoFidelidade:
        pontos = self._repository.saldo(user_id)
        return SaldoFidelidade(
            user_id=user_id,
            pontos=pontos,
            valor_resgate_reais=VALOR_PONTO * pontos,
        )

    def listar_transacoes(self, user_id: str):
        return self._repository.listar_transacoes(user_id)

    def calcular_desconto(
        self,
        user_id: str,
        pontos: int,
        subtotal: Decimal,
    ) -> Decimal:
        if pontos == 0:
            return Decimal("0.00")
        saldo = self._repository.saldo(user_id)
        if pontos > saldo:
            raise HTTPException(422, "Saldo de pontos insuficiente")
        desconto = VALOR_PONTO * pontos
        if desconto > subtotal:
            raise HTTPException(422, "Os pontos nao podem exceder o subtotal do pedido")
        return desconto

    def resgatar(self, user_id: str, pedido_id: str, pontos: int) -> None:
        if pontos == 0:
            return
        try:
            self._repository.resgatar(user_id, pedido_id, pontos)
        except SaldoPontosInsuficienteError as exc:
            raise HTTPException(409, "Saldo de pontos alterado; revise o pedido") from exc

    def creditar_por_pedido(
        self,
        user_id: str,
        pedido_id: str,
        total_pago: Decimal,
    ) -> int:
        pontos = int(total_pago * PONTOS_POR_REAL)
        return self._repository.creditar_por_pedido(user_id, pedido_id, pontos)

    def estornar_resgate(self, user_id: str, pedido_id: str) -> int:
        return self._repository.estornar_resgate(user_id, pedido_id)
