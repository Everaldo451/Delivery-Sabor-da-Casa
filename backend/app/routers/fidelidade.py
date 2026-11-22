from fastapi import APIRouter, Depends

from app.entities.usuario import Usuario
from app.schemas.fidelidade import SaldoFidelidadeOut, TransacaoFidelidadeOut
from app.services.auth_service import AuthService
from app.services.fidelidade_service import FidelidadeService

router = APIRouter(prefix="/fidelidade", tags=["Fidelidade"])
auth_service = AuthService()
fidelidade_service = FidelidadeService()


def get_fidelidade_service() -> FidelidadeService:
    return fidelidade_service


@router.get("", response_model=SaldoFidelidadeOut)
def obter_saldo(
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: FidelidadeService = Depends(get_fidelidade_service),
) -> SaldoFidelidadeOut:
    return SaldoFidelidadeOut.model_validate(
        service.obter_saldo(usuario.id).model_dump()
    )


@router.get("/transacoes", response_model=list[TransacaoFidelidadeOut])
def listar_transacoes(
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: FidelidadeService = Depends(get_fidelidade_service),
) -> list[TransacaoFidelidadeOut]:
    return [
        TransacaoFidelidadeOut.model_validate(transacao.model_dump())
        for transacao in service.listar_transacoes(usuario.id)
    ]
