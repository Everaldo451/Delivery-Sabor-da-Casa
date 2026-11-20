import os
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pymongo import ReturnDocument

from app.auth_stub import Usuario, usuario_logado
from app.cardapio_stub import buscar_prato
from app.database import pedidos_col
from app.pedidos.schemas import (
    AtualizarStatus,
    ItemRepetir,
    PedidoCreate,
    PedidoOut,
    StatusPedido,
)

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

TAXA_ENTREGA = float(os.getenv("TAXA_ENTREGA", "6.0"))
ORDEM_STATUS = list(StatusPedido)  # recebido -> em_preparo -> saiu_para_entrega -> entregue


# ---------- auxiliares ----------
def _para_saida(doc: dict) -> PedidoOut:
    doc = {**doc, "id": str(doc["_id"])}
    doc.pop("_id")
    return PedidoOut(**doc)


def _oid(pedido_id: str) -> ObjectId:
    if not ObjectId.is_valid(pedido_id):
        raise HTTPException(404, "Pedido nao encontrado")
    return ObjectId(pedido_id)


async def _buscar_do_usuario(pedido_id: str, usuario: Usuario) -> dict:
    # Filtrar por user_id garante que um usuario nao ve pedido de outro
    doc = await pedidos_col.find_one({"_id": _oid(pedido_id), "user_id": usuario.id})
    if doc is None:
        raise HTTPException(404, "Pedido nao encontrado")
    return doc


def checar_admin(x_admin_key: str = Header(...)):
    """Protege a troca de status (uso do 'restaurante'). Chave definida em ADMIN_KEY no .env."""
    if x_admin_key != os.getenv("ADMIN_KEY", "troque-esta-chave"):
        raise HTTPException(403, "Chave de administrador invalida")


# ---------- rotas ----------
@router.post("", response_model=PedidoOut, status_code=201)
async def criar_pedido(dados: PedidoCreate, usuario: Usuario = Depends(usuario_logado)):
    itens = []
    for item in dados.itens:
        prato = await buscar_prato(item.prato_id)
        if prato is None or not prato["disponivel"]:
            raise HTTPException(422, f"Prato {item.prato_id} indisponivel")
        # Nome e preco sao COPIADOS pro pedido: o historico nao muda se o cardapio mudar
        itens.append(
            {
                "prato_id": prato["id"],
                "nome": prato["nome"],
                "preco_unitario": prato["preco"],
                "quantidade": item.quantidade,
                "observacao": item.observacao,
            }
        )

    # O total e calculado AQUI, nunca confiando em valores vindos do app
    subtotal = round(sum(i["preco_unitario"] * i["quantidade"] for i in itens), 2)
    desconto = 0.0  # TODO: aplicar cupom/fidelidade quando esse modulo existir
    total = round(subtotal - desconto + TAXA_ENTREGA, 2)

    agora = datetime.now(timezone.utc)
    doc = {
        "user_id": usuario.id,
        "itens": itens,
        "subtotal": subtotal,
        "desconto": desconto,
        "taxa_entrega": TAXA_ENTREGA,
        "total": total,
        "endereco_entrega": dados.endereco_entrega.model_dump(),
        "forma_pagamento": dados.forma_pagamento.value,
        "status": StatusPedido.recebido.value,
        "criado_em": agora,
        "atualizado_em": agora,
    }
    resultado = await pedidos_col.insert_one(doc)
    doc["_id"] = resultado.inserted_id
    return _para_saida(doc)


@router.get("", response_model=list[PedidoOut])
async def historico(
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=50),
    usuario: Usuario = Depends(usuario_logado),
):
    cursor = (
        pedidos_col.find({"user_id": usuario.id})
        .sort("criado_em", -1)
        .skip((pagina - 1) * limite)
        .limit(limite)
    )
    return [_para_saida(doc) async for doc in cursor]


@router.get("/{pedido_id}", response_model=PedidoOut)
async def detalhe_pedido(pedido_id: str, usuario: Usuario = Depends(usuario_logado)):
    return _para_saida(await _buscar_do_usuario(pedido_id, usuario))


@router.get("/{pedido_id}/repetir", response_model=list[ItemRepetir])
async def itens_para_repetir(pedido_id: str, usuario: Usuario = Depends(usuario_logado)):
    """Itens do pedido antigo com o preco atual, para o app jogar no carrinho ('Pedir de novo')."""
    pedido = await _buscar_do_usuario(pedido_id, usuario)
    resultado = []
    for item in pedido["itens"]:
        prato = await buscar_prato(item["prato_id"])
        resultado.append(
            ItemRepetir(
                prato_id=item["prato_id"],
                nome=prato["nome"] if prato else item["nome"],
                preco_atual=prato["preco"] if prato else item["preco_unitario"],
                quantidade=item["quantidade"],
                observacao=item.get("observacao"),
                disponivel=bool(prato and prato["disponivel"]),
            )
        )
    return resultado


@router.patch("/{pedido_id}/status", response_model=PedidoOut, dependencies=[Depends(checar_admin)])
async def atualizar_status(pedido_id: str, dados: AtualizarStatus):
    oid = _oid(pedido_id)
    atual = await pedidos_col.find_one({"_id": oid})
    if atual is None:
        raise HTTPException(404, "Pedido nao encontrado")

    if ORDEM_STATUS.index(dados.status) <= ORDEM_STATUS.index(StatusPedido(atual["status"])):
        raise HTTPException(409, "O status so pode avancar (nao volta nem repete)")

    atualizado = await pedidos_col.find_one_and_update(
        {"_id": oid},
        {"$set": {"status": dados.status.value, "atualizado_em": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )
    return _para_saida(atualizado)
