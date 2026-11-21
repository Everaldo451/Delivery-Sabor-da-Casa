from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.postgresql import criar_tabelas
from app.database.redis import redis_client
from app.repositories.pedido_repository import PedidosRepository
from app.repositories.zona_entrega_repository import ZonaEntregaRepository
from app.routers import include_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_client.ping()
        # Indice pro historico (filtra por usuario, ordena por data)
        await PedidosRepository().criar_indice_historico()
        await ZonaEntregaRepository().criar_indice_geografico()
        criar_tabelas()
        yield
    finally:
        await redis_client.aclose()


app = FastAPI(title="Sabor da Casa - Pedidos", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

include_routers(app)
