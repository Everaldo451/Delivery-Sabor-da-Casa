from datetime import datetime, timezone
from decimal import Decimal

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
    PedidosPaginaOut,
)
from app.repositories.zona_entrega_repository import ZonaEntregaRepository
from app.services.cardapio_service import CardapioService
from app.services.cep_service import (
    CepNaoEncontradoError,
    ViaCepIndisponivelError,
    ViaCepService,
)
from app.services.cupom_service import CupomService
from app.services.fidelidade_service import FidelidadeService
from app.services.pedido_eventos_service import PedidoEventosService


class PedidoService:
    def __init__(
        self,
        pedidos_repository: PedidosRepository,
        zona_entrega_repository: ZonaEntregaRepository,
        cardapio_service: CardapioService,
        payment_strategy_factory: PaymentStrategyFactory | None = None,
        pedido_status_strategy_factory: PedidoStatusStrategyFactory | None = None,
        cupom_service: CupomService | None = None,
        fidelidade_service: FidelidadeService | None = None,
        cep_service: ViaCepService | None = None,
        eventos_service: PedidoEventosService | None = None,
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
        self._cupom_service = cupom_service or CupomService()
        self._fidelidade_service = fidelidade_service or FidelidadeService()
        self._cep_service = cep_service or ViaCepService()
        self._eventos_service = eventos_service or PedidoEventosService()

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
        cep = dados.endereco_entrega.cep
        if cep is None:
            raise HTTPException(422, "CEP do endereco de entrega obrigatorio")
        try:
            await self._cep_service.verificar_cep(cep)
        except CepNaoEncontradoError as exc:
            raise HTTPException(422, "CEP nao encontrado") from exc
        except ViaCepIndisponivelError as exc:
            raise HTTPException(503, "Servico de consulta de CEP indisponivel") from exc

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
        subtotal_decimal = sum(
            (Decimal(str(item.preco_unitario)) * item.quantidade for item in itens),
            start=Decimal("0.00"),
        ).quantize(Decimal("0.01"))
        desconto_cupom = (
            self._cupom_service.calcular_desconto(
                dados.cupom_codigo,
                subtotal_decimal,
                usuario.id,
            )
            if dados.cupom_codigo is not None
            else Decimal("0.00")
        )
        desconto_fidelidade = self._fidelidade_service.calcular_desconto(
            usuario.id,
            dados.pontos_resgatados,
            subtotal_decimal - desconto_cupom,
        )
        desconto_decimal = desconto_cupom + desconto_fidelidade
        subtotal = float(subtotal_decimal)
        desconto = float(desconto_decimal)
        total = round(subtotal_decimal - desconto_decimal + Decimal(str(taxa_entrega)), 2)

        agora = datetime.now(timezone.utc)
        strategy = self._payment_strategy_factory.criar(dados.forma_pagamento)
        pedido = Pedido(
            user_id=usuario.id,
            cupom_codigo=dados.cupom_codigo,
            pontos_resgatados=dados.pontos_resgatados,
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
        persistido = await self._pedidos_repository.inserir(pedido)
        cupom_reservado = False
        try:
            if persistido.id is None and (dados.pontos_resgatados or dados.cupom_codigo):
                raise ValueError("Pedido persistido sem identificador")
            if dados.cupom_codigo:
                self._cupom_service.registrar_uso(
                    dados.cupom_codigo, usuario.id, persistido.id, subtotal_decimal
                )
                cupom_reservado = True
            if dados.pontos_resgatados:
                self._fidelidade_service.resgatar(
                    usuario.id,
                    persistido.id,
                    dados.pontos_resgatados,
                )
        except Exception:
            if cupom_reservado:
                self._cupom_service.estornar_uso(persistido.id)
            if persistido.id is not None:
                await self._pedidos_repository.remover(persistido.id)
            raise
        pedido_saida = self._para_saida(persistido)
        await self._eventos_service.pedido_criado(pedido_saida)
        return pedido_saida

    async def listar_admin(self, pagina: int, limite: int) -> PedidosPaginaOut:
        pedidos, total = await self._pedidos_repository.listar_todos(pagina, limite)
        saidas = [self._para_saida(pedido) for pedido in pedidos]
        total_paginas = (total + limite - 1) // limite
        return PedidosPaginaOut(
            pedidos=saidas,
            pagina=pagina,
            limite=limite,
            total=total,
            total_paginas=total_paginas,
        )

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
        if dados.status == StatusPedido.cancelado and pedido.pontos_resgatados:
            self._fidelidade_service.estornar_resgate(
                pedido.user_id,
                pedido_id,
            )
        if dados.status == StatusPedido.cancelado and pedido.cupom_codigo:
            self._cupom_service.estornar_uso(pedido_id)
        pedido_saida = self._para_saida(atualizado)
        await self._eventos_service.status_atualizado(pedido_saida)
        return pedido_saida

    async def confirmar_pagamento(self, pedido_id: str) -> PedidoOut:
        pedido = await self._buscar_por_id(pedido_id)
        strategy = self._pedido_status_strategy_factory.criar(pedido.status)
        if not strategy.permite_transicao(
            StatusPedido.recebido,
            pagamento_aprovado=True,
        ):
            return self._para_saida(pedido)
        atualizado = await self._salvar_status(pedido_id, StatusPedido.recebido)
        pedido_saida = self._para_saida(atualizado)
        await self._eventos_service.status_atualizado(pedido_saida)
        return pedido_saida

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
