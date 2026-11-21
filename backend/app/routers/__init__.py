from fastapi import FastAPI


def include_routers(app: FastAPI) -> None:
    from app.routers.pedidos import router as pedidos_router
    from app.routers.payments import router as payments_router

    app.include_router(pedidos_router)
    app.include_router(payments_router)