from fastapi import APIRouter, Depends, Response, status

from app.entities.usuario import Usuario
from app.schemas.cupons import (
    CupomAtualizar,
    CupomCreate,
    CupomDescontoOut,
    CupomOut,
    CupomValidarIn,
)
from app.services.auth_service import AuthService
from app.services.cupom_service import CupomService

router = APIRouter(prefix="/cupons", tags=["Cupons"])
auth_service = AuthService()
cupom_service = CupomService()


def get_cupom_service() -> CupomService:
    return cupom_service


@router.get("", response_model=list[CupomOut])
def listar_cupons(
    service: CupomService = Depends(get_cupom_service),
) -> list[CupomOut]:
    return service.listar()


@router.get("/admin", response_model=list[CupomOut])
def listar_todos_cupons(
    _: Usuario = Depends(auth_service.usuario_admin),
    service: CupomService = Depends(get_cupom_service),
) -> list[CupomOut]:
    return service.listar_todos()


@router.post("/validar", response_model=CupomDescontoOut)
def validar_cupom(
    dados: CupomValidarIn,
    usuario: Usuario = Depends(auth_service.usuario_logado),
    service: CupomService = Depends(get_cupom_service),
) -> CupomDescontoOut:
    desconto = service.calcular_desconto(dados.codigo, dados.subtotal, usuario.id)
    return CupomDescontoOut(codigo=dados.codigo, desconto=desconto)


@router.post("", response_model=CupomOut, status_code=status.HTTP_201_CREATED)
def criar_cupom(
    dados: CupomCreate,
    _: Usuario = Depends(auth_service.usuario_admin),
    service: CupomService = Depends(get_cupom_service),
) -> CupomOut:
    return service.criar(dados)


@router.put("/{cupom_id}", response_model=CupomOut)
def atualizar_cupom(
    cupom_id: int,
    dados: CupomAtualizar,
    _: Usuario = Depends(auth_service.usuario_admin),
    service: CupomService = Depends(get_cupom_service),
) -> CupomOut:
    return service.atualizar(cupom_id, dados)


@router.delete("/{cupom_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_cupom(
    cupom_id: int,
    _: Usuario = Depends(auth_service.usuario_admin),
    service: CupomService = Depends(get_cupom_service),
) -> Response:
    service.remover(cupom_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
