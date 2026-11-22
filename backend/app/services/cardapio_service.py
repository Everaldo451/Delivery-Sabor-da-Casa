from fastapi import HTTPException

from app.entities.cardapio import Categoria, ImagemPrato, Prato
from app.repositories.cardapio_repository import (
    CardapioRepository,
    CategoriaEmUsoError,
    CategoriaJaExisteError,
    CategoriaNaoEncontradaError,
)
from app.schemas.cardapio import (
    CategoriaAtualizar,
    CategoriaCreate,
    CategoriaOut,
    ImagemPratoOut,
    PratoAtualizar,
    PratoCreate,
    PratoOut,
)

TAMANHO_MAXIMO_IMAGEM_BYTES = 5 * 1024 * 1024
TIPOS_IMAGEM_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}


class CardapioService:
    def __init__(self, repository: CardapioRepository | None = None) -> None:
        self._repository = repository or CardapioRepository()

    def listar_categorias(self) -> list[CategoriaOut]:
        categorias = self._repository.listar_categorias()
        return [
            CategoriaOut.model_validate(categoria.model_dump())
            for categoria in categorias
        ]

    def criar_categoria(self, dados: CategoriaCreate) -> CategoriaOut:
        try:
            categoria = self._repository.inserir_categoria(dados.nome)
        except CategoriaJaExisteError as exc:
            raise HTTPException(409, "Categoria ja cadastrada") from exc
        return self._categoria_para_saida(categoria)

    def atualizar_categoria(
        self,
        categoria_id: int,
        dados: CategoriaAtualizar,
    ) -> CategoriaOut:
        try:
            categoria = self._repository.atualizar_categoria(
                categoria_id,
                dados.nome,
            )
        except CategoriaJaExisteError as exc:
            raise HTTPException(409, "Ja existe uma categoria com esse nome") from exc
        if categoria is None:
            raise HTTPException(404, "Categoria nao encontrada")
        return self._categoria_para_saida(categoria)

    def remover_categoria(self, categoria_id: int) -> None:
        try:
            removida = self._repository.remover_categoria(categoria_id)
        except CategoriaEmUsoError as exc:
            raise HTTPException(
                409,
                "Nao e possivel remover uma categoria que possui pratos",
            ) from exc
        if not removida:
            raise HTTPException(404, "Categoria nao encontrada")

    def listar_pratos(self, categoria: str | None = None) -> list[PratoOut]:
        pratos = self._repository.listar_pratos(categoria)
        return [self._para_saida(prato) for prato in pratos]

    def buscar_prato_por_id(self, prato_id: str) -> PratoOut:
        prato = self._repository.buscar_prato(prato_id)
        if prato is None:
            raise HTTPException(404, "Prato nao encontrado")
        return self._para_saida(prato)

    def salvar_imagem(
        self,
        prato_id: str,
        dados: bytes,
        content_type: str,
    ) -> PratoOut:
        if not dados:
            raise HTTPException(422, "A imagem nao pode estar vazia")
        if len(dados) > TAMANHO_MAXIMO_IMAGEM_BYTES:
            raise HTTPException(413, "A imagem deve ter no maximo 5 MiB")
        if content_type not in TIPOS_IMAGEM_PERMITIDOS:
            raise HTTPException(415, "Formato aceito: JPEG, PNG ou WebP")
        if not self._assinatura_compativel(dados, content_type):
            raise HTTPException(422, "O conteudo nao corresponde ao formato informado")
        imagem = ImagemPrato(
            imagem=dados,
            content_type=content_type,
        )
        if not self._repository.salvar_imagem(prato_id, imagem):
            raise HTTPException(404, "Prato nao encontrado")
        return self.buscar_prato_por_id(prato_id)

    def buscar_imagem(self, prato_id: str) -> ImagemPrato:
        imagem = self._repository.buscar_imagem(prato_id)
        if imagem is None:
            raise HTTPException(404, "Imagem nao encontrada")
        return imagem

    def remover_imagem(self, prato_id: str) -> None:
        if not self._repository.remover_imagem(prato_id):
            raise HTTPException(404, "Prato nao encontrado")

    async def buscar_prato(self, prato_id: str) -> dict | None:
        """Consulta usada por pedidos; preço e disponibilidade vêm do SQL."""
        prato = self._repository.buscar_prato(prato_id)
        if prato is None:
            return None
        if prato.id is None:
            raise ValueError("Prato persistido sem identificador")
        return {
            "id": prato.id,
            "nome": prato.nome,
            "preco": float(prato.preco),
            "disponivel": prato.disponivel,
        }

    def criar_prato(self, dados: PratoCreate) -> PratoOut:
        try:
            prato = self._repository.inserir_prato(
                Prato(**dados.model_dump())
            )
        except CategoriaNaoEncontradaError as exc:
            raise HTTPException(404, "Categoria nao encontrada") from exc
        return self._para_saida(prato)

    def atualizar_prato(self, prato_id: str, dados: PratoAtualizar) -> PratoOut:
        try:
            prato = self._repository.atualizar_prato(
                Prato(
                    id=prato_id,
                    **dados.model_dump(),
                )
            )
        except CategoriaNaoEncontradaError as exc:
            raise HTTPException(404, "Categoria nao encontrada") from exc
        if prato is None:
            raise HTTPException(404, "Prato nao encontrado")
        return self._para_saida(prato)

    def remover_prato(self, prato_id: str) -> None:
        if not self._repository.remover_prato(prato_id):
            raise HTTPException(404, "Prato nao encontrado")

    @staticmethod
    def _categoria_para_saida(categoria: Categoria) -> CategoriaOut:
        return CategoriaOut.model_validate(categoria.model_dump())

    @staticmethod
    def _assinatura_compativel(dados: bytes, content_type: str) -> bool:
        if content_type == "image/jpeg":
            return dados.startswith(b"\xff\xd8\xff")
        if content_type == "image/png":
            return dados.startswith(b"\x89PNG\r\n\x1a\n")
        if content_type == "image/webp":
            return (
                len(dados) >= 12
                and dados[:4] == b"RIFF"
                and dados[8:12] == b"WEBP"
            )
        return False

    @staticmethod
    def _para_saida(prato: Prato) -> PratoOut:
        if prato.id is None:
            raise ValueError("Prato sem identificador persistido")
        imagem = (
            ImagemPratoOut(
                url=f"/cardapio/{prato.id}/imagem",
                content_type=prato.imagem.content_type,
            )
            if prato.imagem is not None
            else None
        )
        return PratoOut(
            id=prato.id,
            nome=prato.nome,
            descricao=prato.descricao,
            preco=prato.preco,
            categoria=prato.categoria,
            imagem=imagem,
            disponivel=prato.disponivel,
        )
