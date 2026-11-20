from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import pedidos_col
from app.pedidos.router import router as pedidos_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Indice pro historico (filtra por usuario, ordena por data)
    await pedidos_col.create_index([("user_id", 1), ("criado_em", -1)])
    yield


app = FastAPI(title="Sabor da Casa - Pedidos", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

app.include_router(pedidos_router)
