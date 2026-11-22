from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.schemas.cardapio import (
    CategoriaAtualizar,
    CategoriaCreate,
    CategoriaOut,
    PratoAtualizar,
    PratoCreate,
    PratoOut,
)
from app.services.auth_service import AuthService
from app.services.cardapio_service import (
    TAMANHO_MAXIMO_IMAGEM_BYTES,
    CardapioService,
)

router = APIRouter(prefix="/cardapio", tags=["Cardapio"])

auth_service = AuthService()
cardapio_service = CardapioService()


def get_cardapio_service() -> CardapioService:
    return cardapio_service


async def _ler_imagem(request: Request) -> bytes:
    tamanho_declarado = request.headers.get("content-length")
    if tamanho_declarado is not None:
        try:
            if int(tamanho_declarado) > TAMANHO_MAXIMO_IMAGEM_BYTES:
                raise HTTPException(413, "A imagem deve ter no maximo 5 MiB")
        except ValueError as exc:
            raise HTTPException(400, "Content-Length invalido") from exc

    partes: list[bytes] = []
    tamanho = 0
    async for parte in request.stream():
        tamanho += len(parte)
        if tamanho > TAMANHO_MAXIMO_IMAGEM_BYTES:
            raise HTTPException(413, "A imagem deve ter no maximo 5 MiB")
        partes.append(parte)
    return b"".join(partes)


@router.get("/categorias", response_model=list[CategoriaOut])
def listar_categorias(
    service: CardapioService = Depends(get_cardapio_service),
) -> list[CategoriaOut]:
    return service.listar_categorias()


@router.post(
    "/categorias",
    response_model=CategoriaOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth_service.usuario_admin)],
)
def criar_categoria(
    dados: CategoriaCreate,
    service: CardapioService = Depends(get_cardapio_service),
) -> CategoriaOut:
    return service.criar_categoria(dados)


@router.put(
    "/categorias/{categoria_id}",
    response_model=CategoriaOut,
    dependencies=[Depends(auth_service.usuario_admin)],
)
def atualizar_categoria(
    categoria_id: int,
    dados: CategoriaAtualizar,
    service: CardapioService = Depends(get_cardapio_service),
) -> CategoriaOut:
    return service.atualizar_categoria(categoria_id, dados)


@router.delete(
    "/categorias/{categoria_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth_service.usuario_admin)],
)
def remover_categoria(
    categoria_id: int,
    service: CardapioService = Depends(get_cardapio_service),
) -> Response:
    service.remover_categoria(categoria_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("", response_model=list[PratoOut])
def listar_pratos(
    categoria: str | None = Query(default=None),
    service: CardapioService = Depends(get_cardapio_service),
) -> list[PratoOut]:
    return service.listar_pratos(categoria)


@router.get("/{prato_id}/imagem", response_class=Response)
def obter_imagem_prato(
    prato_id: str,
    service: CardapioService = Depends(get_cardapio_service),
) -> Response:
    imagem = service.buscar_imagem(prato_id)
    return Response(
        content=imagem.imagem,
        media_type=imagem.content_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.put(
    "/{prato_id}/imagem",
    response_model=PratoOut,
    dependencies=[Depends(auth_service.usuario_admin)],
)
async def salvar_imagem_prato(
    prato_id: str,
    request: Request,
    service: CardapioService = Depends(get_cardapio_service),
) -> PratoOut:
    content_type = (
        request.headers.get("content-type", "")
        .split(";", 1)[0]
        .strip()
        .lower()
    )
    dados = await _ler_imagem(request)
    return service.salvar_imagem(prato_id, dados, content_type)


@router.delete(
    "/{prato_id}/imagem",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth_service.usuario_admin)],
)
def remover_imagem_prato(
    prato_id: str,
    service: CardapioService = Depends(get_cardapio_service),
) -> Response:
    service.remover_imagem(prato_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{prato_id}", response_model=PratoOut)
def detalhe_prato(
    prato_id: str,
    service: CardapioService = Depends(get_cardapio_service),
) -> PratoOut:
    return service.buscar_prato_por_id(prato_id)


@router.post(
    "",
    response_model=PratoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth_service.usuario_admin)],
)
def criar_prato(
    dados: PratoCreate,
    service: CardapioService = Depends(get_cardapio_service),
) -> PratoOut:
    return service.criar_prato(dados)


@router.put(
    "/{prato_id}",
    response_model=PratoOut,
    dependencies=[Depends(auth_service.usuario_admin)],
)
def atualizar_prato(
    prato_id: str,
    dados: PratoAtualizar,
    service: CardapioService = Depends(get_cardapio_service),
) -> PratoOut:
    return service.atualizar_prato(prato_id, dados)


@router.delete(
    "/{prato_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth_service.usuario_admin)],
)
def remover_prato(
    prato_id: str,
    service: CardapioService = Depends(get_cardapio_service),
) -> Response:
    service.remover_prato(prato_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
