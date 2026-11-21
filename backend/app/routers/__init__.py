from fastapi import FastAPI


def include_routers(app: FastAPI) -> None:
    from app.routers.pedidos import router as pedidos_router

    app.include_router(pedidos_router)