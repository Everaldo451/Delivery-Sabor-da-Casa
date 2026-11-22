from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import load_only
from sqlmodel import Session

from app.database.postgresql import create_session
from app.database.postgresql.models.cardapio import CategoriaModel, PratoModel
from app.entities.cardapio import Categoria, ImagemPrato, Prato


class CategoriaNaoEncontradaError(Exception):
    pass


class CategoriaJaExisteError(Exception):
    pass


class CategoriaEmUsoError(Exception):
    pass


class CardapioRepository:
    def listar_categorias(self) -> list[Categoria]:
        with create_session() as session:
            categorias = session.exec(
                select(CategoriaModel).order_by(CategoriaModel.id)
            ).all()
            return [
                self._categoria_para_entidade(categoria)
                for categoria in categorias
            ]

    def inserir_categoria(self, nome: str) -> Categoria:
        nome = nome.strip()
        with create_session() as session:
            existente = self._buscar_categoria_por_nome(session, nome)
            if existente is not None:
                raise CategoriaJaExisteError(nome)

            categoria = CategoriaModel(nome=nome)
            session.add(categoria)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise CategoriaJaExisteError(nome) from exc
            session.refresh(categoria)
            return self._categoria_para_entidade(categoria)

    def atualizar_categoria(self, categoria_id: int, nome: str) -> Categoria | None:
        nome = nome.strip()
        with create_session() as session:
            categoria = session.get(CategoriaModel, categoria_id)
            if categoria is None:
                return None

            existente = self._buscar_categoria_por_nome(session, nome)
            if existente is not None and existente.id != categoria_id:
                raise CategoriaJaExisteError(nome)

            categoria.nome = nome
            session.add(categoria)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise CategoriaJaExisteError(nome) from exc
            session.refresh(categoria)
            return self._categoria_para_entidade(categoria)

    def remover_categoria(self, categoria_id: int) -> bool:
        with create_session() as session:
            categoria = session.get(CategoriaModel, categoria_id)
            if categoria is None:
                return False

            quantidade_pratos = session.exec(
                select(func.count())
                .select_from(PratoModel)
                .where(PratoModel.categoria_id == categoria_id)
            ).one()
            if quantidade_pratos:
                raise CategoriaEmUsoError(categoria_id)

            session.delete(categoria)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise CategoriaEmUsoError(categoria_id) from exc
            return True

    def listar_pratos(self, categoria: str | None = None) -> list[Prato]:
        statement = (
            select(PratoModel)
            .options(self._opcoes_sem_imagem())
            .join(CategoriaModel)
            .order_by(CategoriaModel.id, PratoModel.nome)
        )
        if categoria is not None:
            statement = statement.where(
                func.lower(CategoriaModel.nome) == categoria.strip().casefold()
            )

        with create_session() as session:
            pratos = session.exec(statement).all()
            return [self._prato_para_entidade(prato) for prato in pratos]

    def buscar_prato(self, prato_id: str) -> Prato | None:
        with create_session() as session:
            prato = session.exec(
                select(PratoModel)
                .where(PratoModel.id == prato_id)
                .options(self._opcoes_sem_imagem())
            ).first()
            return self._prato_para_entidade(prato) if prato is not None else None

    def buscar_imagem(self, prato_id: str) -> ImagemPrato | None:
        with create_session() as session:
            imagem = session.exec(
                select(
                    PratoModel.imagem,
                    PratoModel.imagem_content_type,
                ).where(PratoModel.id == prato_id)
            ).first()
            if imagem is None:
                return None
            dados, content_type = imagem
            if dados is None or content_type is None:
                return None
            return ImagemPrato(imagem=bytes(dados), content_type=content_type)

    def salvar_imagem(self, prato_id: str, imagem: ImagemPrato) -> bool:
        if imagem.imagem is None:
            raise ValueError("A entidade ImagemPrato precisa conter os bytes")
        with create_session() as session:
            resultado = session.exec(
                update(PratoModel)
                .where(PratoModel.id == prato_id)
                .values(
                    imagem=imagem.imagem,
                    imagem_content_type=imagem.content_type,
                )
            )
            if resultado.rowcount == 0:
                return False
            session.commit()
            return True

    def remover_imagem(self, prato_id: str) -> bool:
        with create_session() as session:
            resultado = session.exec(
                update(PratoModel)
                .where(PratoModel.id == prato_id)
                .values(
                    imagem=None,
                    imagem_content_type=None,
                )
            )
            if resultado.rowcount == 0:
                return False
            session.commit()
            return True

    def inserir_prato(self, prato: Prato) -> Prato:
        with create_session() as session:
            categoria_model = self._buscar_categoria(session, prato.categoria)
            imagem = prato.imagem
            prato_model = PratoModel(
                id=prato.id or str(uuid4()),
                nome=prato.nome,
                descricao=prato.descricao,
                preco=prato.preco,
                categoria_id=categoria_model.id,
                imagem=imagem.imagem if imagem is not None else None,
                imagem_content_type=(
                    imagem.content_type
                    if imagem is not None and imagem.imagem is not None
                    else None
                ),
                disponivel=prato.disponivel,
            )
            session.add(prato_model)
            session.commit()
            session.refresh(prato_model)
            return self._prato_para_entidade(prato_model)

    def atualizar_prato(self, prato: Prato) -> Prato | None:
        if prato.id is None:
            return None
        with create_session() as session:
            prato_model = session.get(PratoModel, prato.id)
            if prato_model is None:
                return None
            categoria_model = self._buscar_categoria(session, prato.categoria)
            prato_model.nome = prato.nome
            prato_model.descricao = prato.descricao
            prato_model.preco = prato.preco
            prato_model.categoria_id = categoria_model.id
            prato_model.disponivel = prato.disponivel
            session.add(prato_model)
            session.commit()
            session.refresh(prato_model)
            return self._prato_para_entidade(prato_model)

    def remover_prato(self, prato_id: str) -> bool:
        with create_session() as session:
            prato = session.get(PratoModel, prato_id)
            if prato is None:
                return False
            session.delete(prato)
            session.commit()
            return True

    @staticmethod
    def _buscar_categoria(session: Session, nome: str) -> CategoriaModel:
        categoria = CardapioRepository._buscar_categoria_por_nome(session, nome)
        if categoria is None:
            raise CategoriaNaoEncontradaError(nome)
        return categoria

    @staticmethod
    def _buscar_categoria_por_nome(
        session: Session,
        nome: str,
    ) -> CategoriaModel | None:
        return session.exec(
            select(CategoriaModel).where(
                func.lower(CategoriaModel.nome) == nome.strip().casefold()
            )
        ).first()

    @staticmethod
    def _categoria_para_entidade(categoria: CategoriaModel) -> Categoria:
        return Categoria(id=categoria.id, nome=categoria.nome)

    @staticmethod
    def _opcoes_sem_imagem():
        return load_only(
            PratoModel.id,
            PratoModel.nome,
            PratoModel.descricao,
            PratoModel.preco,
            PratoModel.categoria_id,
            PratoModel.imagem_content_type,
            PratoModel.disponivel,
        )

    @staticmethod
    def _prato_para_entidade(prato: PratoModel) -> Prato:
        return Prato(
            id=prato.id,
            nome=prato.nome,
            descricao=prato.descricao,
            preco=prato.preco,
            categoria=prato.categoria.nome,
            imagem=(
                ImagemPrato(
                    content_type=prato.imagem_content_type,
                )
                if prato.imagem_content_type is not None
                else None
            ),
            disponivel=prato.disponivel,
        )
