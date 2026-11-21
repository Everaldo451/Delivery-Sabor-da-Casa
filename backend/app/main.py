from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.repositories.pedido_repository import PedidosRepository
from app.repositories.zona_entrega_repository import ZonaEntregaRepository
from app.routers import include_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Indice pro historico (filtra por usuario, ordena por data)
    await PedidosRepository().criar_indice_historico()
    await ZonaEntregaRepository().criar_indice_geografico()
    yield


app = FastAPI(title="Sabor da Casa - Pedidos", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

include_routers(app)
