from fastapi import HTTPException

from app.entities.favorito import Favorito
from app.repositories.favorito_repository import FavoritoRepository


class FavoritoService:
    def __init__(self, repository: FavoritoRepository | None = None) -> None:
        self._repository = repository or FavoritoRepository()

    def listar(self, user_id: str) -> list[Favorito]:
        return self._repository.listar(user_id)

    def adicionar(self, user_id: str, prato_id: str) -> Favorito:
        favorito = self._repository.adicionar(user_id, prato_id)
        if favorito is None:
            raise HTTPException(404, "Prato nao encontrado")
        return favorito

    def remover(self, user_id: str, prato_id: str) -> None:
        if not self._repository.remover(user_id, prato_id):
            raise HTTPException(404, "Favorito nao encontrado")
