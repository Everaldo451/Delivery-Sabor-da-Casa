from fastapi import FastAPI


def include_routers(app: FastAPI) -> None:
    from app.routers.auth import router as auth_router
    from app.routers.carrinho import router as carrinho_router
    from app.routers.cardapio import router as cardapio_router
    from app.routers.cupons import router as cupons_router
    from app.routers.favoritos import router as favoritos_router
    from app.routers.fidelidade import router as fidelidade_router
    from app.routers.pedidos import router as pedidos_router
    from app.routers.payments import router as payments_router
    from app.routers.users import router as users_router
    from app.routers.zonas_entrega import router as zonas_entrega_router

    app.include_router(auth_router)
    app.include_router(carrinho_router)
    app.include_router(cardapio_router)
    app.include_router(favoritos_router)
    app.include_router(cupons_router)
    app.include_router(fidelidade_router)
    app.include_router(pedidos_router)
    app.include_router(payments_router)
    app.include_router(users_router)
    app.include_router(zonas_entrega_router)
