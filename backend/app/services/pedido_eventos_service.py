import logging

from fastapi import HTTPException, WebSocket
from starlette.websockets import WebSocketDisconnect

from app.services.auth_service import AuthService
from app.schemas.pedidos import PedidoOut

logger = logging.getLogger(__name__)


class PedidoEventosService:
    """Gerencia conexoes administrativas e publica eventos de pedidos."""

    def __init__(self, auth_service: AuthService | None = None) -> None:
        self._auth_service = auth_service or AuthService()
        self._conexoes: set[WebSocket] = set()

    async def acompanhar(self, websocket: WebSocket, token: str) -> None:
        try:
            usuario = await self._auth_service.usuario_por_token(token)
        except HTTPException as exc:
            codigo = 4403 if exc.status_code == 403 else 4401
            await websocket.close(code=codigo)
            return

        if not usuario.is_admin:
            await websocket.close(code=4403)
            return

        await websocket.accept()
        self._conexoes.add(websocket)
        try:
            while True:
                mensagem = await websocket.receive_text()
                if mensagem == "ping":
                    await websocket.send_json({"evento": "pong"})
        except WebSocketDisconnect:
            pass
        finally:
            self._conexoes.discard(websocket)

    async def pedido_criado(self, pedido: PedidoOut) -> None:
        await self._publicar("pedido_criado", pedido)

    async def status_atualizado(self, pedido: PedidoOut) -> None:
        await self._publicar("pedido_status_atualizado", pedido)

    async def _publicar(self, evento: str, pedido: PedidoOut) -> None:
        mensagem = {
            "evento": evento,
            "pedido": pedido.model_dump(mode="json"),
        }
        desconectadas = []
        for websocket in tuple(self._conexoes):
            try:
                await websocket.send_json(mensagem)
            except Exception:
                logger.exception("Falha ao publicar evento de pedido")
                desconectadas.append(websocket)
        for websocket in desconectadas:
            self._conexoes.discard(websocket)
