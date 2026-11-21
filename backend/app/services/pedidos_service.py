from datetime import datetime, timezone

from fastapi import HTTPException

from app.entities.pedido import ItemPedido, Pedido, StatusPedido
from app.entities.usuario import Usuario
from app.factories.payment_strategy_factory import PaymentStrategyFactory
from app.factories.pedido_status_strategy_factory import PedidoStatusStrategyFactory
from app.repositories.pedido_repository import PedidosRepository
from app.schemas.pedidos import (
    AtualizarStatus,
    ItemRepetir,
    PedidoCreate,
    PedidoOut,
)
from app.repositories.zona_entrega_repository import ZonaEntregaRepository
from app.services.cardapio_service import CardapioService


class PedidoService:
    def __init__(
        self,
        pedidos_repository: PedidosRepository,
        zona_entrega_repository: ZonaEntregaRepository,
        cardapio_service: CardapioService,
        payment_strategy_factory: PaymentStrategyFactory | None = None,
        pedido_status_strategy_factory: PedidoStatusStrategyFactory | None = None,
    ) -> None:
        self._pedidos_repository = pedidos_repository
        self._zona_entrega_repository = zona_entrega_repository
        self._cardapio_service = cardapio_service
        self._payment_strategy_factory = (
            payment_strategy_factory or PaymentStrategyFactory()
        )
        self._pedido_status_strategy_factory = (
            pedido_status_strategy_factory or PedidoStatusStrategyFactory()
        )

    def _para_saida(self, pedido: Pedido) -> PedidoOut:
        if pedido.id is None:
            raise ValueError("Pedido sem identificador persistido")
        return PedidoOut.model_validate(pedido.model_dump())

    async def _buscar_do_usuario(self, pedido_id: str, usuario: Usuario) -> Pedido:
        pedido = await self._pedidos_repository.buscar_do_usuario(pedido_id, usuario.id)
        if pedido is None:
            raise HTTPException(404, "Pedido nao encontrado")
        return pedido

    async def _calcular_taxa_entrega(self, dados: PedidoCreate) -> float:
        localizacao = dados.endereco_entrega.localizacao
        if localizacao is None:
            raise HTTPException(422, "Localizacao do endereco de entrega obrigatoria")

        zonas = await self._zona_entrega_repository.buscar_por_localizacao(localizacao)
        if not zonas:
            raise HTTPException(422, "Endereco fora da area de entrega")
        if len(zonas) > 1:
            raise HTTPException(
                409, "Endereco pertence a mais de uma zona de entrega"
            )
        return zonas[0].valor

    async def criar_pedido(self, dados: PedidoCreate, usuario: Usuario) -> PedidoOut:
        taxa_entrega = await self._calcular_taxa_entrega(dados)
        itens: list[ItemPedido] = []
        for item in dados.itens:
            prato = await self._cardapio_service.buscar_prato(item.prato_id)
            if prato is None or not prato["disponivel"]:
                raise HTTPException(422, f"Prato {item.prato_id} indisponivel")
            # Nome e preco sao COPIADOS pro pedido: o historico nao muda se o cardapio mudar
            itens.append(
                ItemPedido(
                    prato_id=prato["id"],
                    nome=prato["nome"],
                    preco_unitario=prato["preco"],
                    quantidade=item.quantidade,
                    observacao=item.observacao,
                )
            )

        # O total e calculado AQUI, nunca confiando em valores vindos do app
        subtotal = round(sum(i.preco_unitario * i.quantidade for i in itens), 2)
        desconto = 0.0  # TODO: aplicar cupom/fidelidade quando esse modulo existir
        total = round(subtotal - desconto + taxa_entrega, 2)

        agora = datetime.now(timezone.utc)
        strategy = self._payment_strategy_factory.criar(dados.forma_pagamento)
        pedido = Pedido(
            user_id=usuario.id,
            itens=itens,
            subtotal=subtotal,
            desconto=desconto,
            taxa_entrega=taxa_entrega,
            total=total,
            endereco_entrega=dados.endereco_entrega,
            forma_pagamento=dados.forma_pagamento,
            status=strategy.status_inicial_pedido(),
            criado_em=agora,
            atualizado_em=agora,
        )
        return self._para_saida(await self._pedidos_repository.inserir(pedido))

    async def historico(
        self, pagina: int, limite: int, usuario: Usuario
    ) -> list[PedidoOut]:
        docs = await self._pedidos_repository.listar_por_usuario(
            usuario.id, pagina, limite
        )
        return [self._para_saida(pedido) for pedido in docs]

    async def detalhe_pedido(self, pedido_id: str, usuario: Usuario) -> PedidoOut:
        doc = await self._buscar_do_usuario(pedido_id, usuario)
        return self._para_saida(doc)

    async def itens_para_repetir(
        self, pedido_id: str, usuario: Usuario
    ) -> list[ItemRepetir]:
        pedido = await self._buscar_do_usuario(pedido_id, usuario)
        resultado = []
        for item in pedido.itens:
            prato = await self._cardapio_service.buscar_prato(item.prato_id)
            resultado.append(
                ItemRepetir(
                    prato_id=item.prato_id,
                    nome=prato["nome"] if prato else item.nome,
                    preco_atual=prato["preco"] if prato else item.preco_unitario,
                    quantidade=item.quantidade,
                    observacao=item.observacao,
                    disponivel=bool(prato and prato["disponivel"]),
                )
            )
        return resultado

    async def atualizar_status(
        self, pedido_id: str, dados: AtualizarStatus
    ) -> PedidoOut:
        pedido = await self._buscar_por_id(pedido_id)
        strategy = self._pedido_status_strategy_factory.criar(pedido.status)
        if not strategy.permite_transicao(dados.status):
            raise HTTPException(
                409,
                f"Transicao de status nao permitida: "
                f"{pedido.status.value} -> {dados.status.value}",
            )
        atualizado = await self._salvar_status(pedido_id, dados.status)
        return self._para_saida(atualizado)

    async def confirmar_pagamento(self, pedido_id: str) -> PedidoOut:
        pedido = await self._buscar_por_id(pedido_id)
        strategy = self._pedido_status_strategy_factory.criar(pedido.status)
        if not strategy.permite_transicao(
            StatusPedido.recebido,
            pagamento_aprovado=True,
        ):
            return self._para_saida(pedido)
        atualizado = await self._salvar_status(pedido_id, StatusPedido.recebido)
        return self._para_saida(atualizado)

    async def _buscar_por_id(self, pedido_id: str) -> Pedido:
        pedido = await self._pedidos_repository.buscar_por_id(pedido_id)
        if pedido is None:
            raise HTTPException(404, "Pedido nao encontrado")
        return pedido

    async def _salvar_status(
        self,
        pedido_id: str,
        status: StatusPedido,
    ) -> Pedido:
        atualizado = await self._pedidos_repository.atualizar_status(
            pedido_id,
            status,
            datetime.now(timezone.utc),
        )
        if atualizado is None:
            raise HTTPException(404, "Pedido nao encontrado")
        return atualizado
