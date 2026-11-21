"""
PROVISORIO: simula a consulta de pratos enquanto o modulo de cardapio nao fica pronto.

Troque `buscar_prato` por uma consulta real ao cardapio. Ela deve devolver um dict com:
    id (str), nome (str), preco (float), disponivel (bool)
ou None se o prato nao existir.
"""

PRATOS = {
    "1": {"id": "1", "nome": "Feijoada completa", "preco": 39.90, "disponivel": True},
    "2": {"id": "2", "nome": "Strogonoff de frango", "preco": 32.50, "disponivel": True},
    "3": {"id": "3", "nome": "Suco de laranja 500ml", "preco": 9.00, "disponivel": True},
    "4": {"id": "4", "nome": "Pudim de leite", "preco": 12.00, "disponivel": True},
    "5": {"id": "5", "nome": "Moqueca de peixe", "preco": 54.00, "disponivel": False},
}


class CardapioService:
    async def buscar_prato(self, prato_id: str) -> dict | None:
        return PRATOS.get(prato_id)
