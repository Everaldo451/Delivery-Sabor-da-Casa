from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.postgresql import create_session
from app.database.postgresql.models.cupom import CupomModel
from app.database.postgresql.models.cupom_uso import CupomUsoModel
from app.database.postgresql.models.payment import PaymentModel
from app.entities.payment import PaymentStatus
from app.entities.cupom import Cupom


class CodigoCupomDuplicadoError(Exception):
    pass


class UsoCupomIndisponivelError(Exception):
    pass


class CupomRepository:
    def listar(self) -> list[Cupom]:
        with create_session() as session:
            cupons = session.exec(select(CupomModel).order_by(CupomModel.codigo)).all()
            return [self._para_entidade(cupom) for cupom in cupons]

    def buscar_por_codigo(self, codigo: str) -> Cupom | None:
        with create_session() as session:
            cupom = session.exec(
                select(CupomModel).where(CupomModel.codigo == codigo)
            ).first()
            return self._para_entidade(cupom) if cupom is not None else None

    def inserir(self, cupom: Cupom) -> Cupom:
        modelo = self._para_modelo(cupom)
        with create_session() as session:
            session.add(modelo)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise CodigoCupomDuplicadoError(cupom.codigo) from exc
            session.refresh(modelo)
            return self._para_entidade(modelo)

    def atualizar(self, cupom: Cupom) -> Cupom | None:
        if cupom.id is None:
            return None
        with create_session() as session:
            modelo = session.get(CupomModel, cupom.id)
            if modelo is None:
                return None
            self._copiar_para_modelo(cupom, modelo)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise CodigoCupomDuplicadoError(cupom.codigo) from exc
            session.refresh(modelo)
            return self._para_entidade(modelo)

    def remover(self, cupom_id: int) -> bool:
        with create_session() as session:
            modelo = session.get(CupomModel, cupom_id)
            if modelo is None:
                return False
            modelo.ativo = False
            session.commit()
            return True

    def validar_disponibilidade(self, cupom_id: int, user_id: str) -> None:
        with create_session() as session:
            self._validar_limites(session, cupom_id, user_id)

    def registrar_uso(
        self, codigo: str, user_id: str, pedido_id: str, subtotal: Decimal
    ) -> None:
        with create_session() as session:
            cupom = session.exec(
                select(CupomModel)
                .where(CupomModel.codigo == codigo)
                .with_for_update()
            ).first()
            hoje = datetime.now(timezone.utc).date()
            if (
                cupom is None
                or not cupom.ativo
                or (cupom.valido_de is not None and cupom.valido_de > hoje)
                or (cupom.valido_ate is not None and cupom.valido_ate < hoje)
                or (cupom is not None and subtotal < cupom.subtotal_minimo)
            ):
                raise UsoCupomIndisponivelError("Cupom indisponivel")
            existente = session.exec(
                select(CupomUsoModel).where(
                    CupomUsoModel.cupom_id == cupom.id,
                    CupomUsoModel.pedido_id == pedido_id,
                )
            ).first()
            if existente is not None:
                return
            self._validar_limites(session, cupom.id, user_id)
            session.add(CupomUsoModel(cupom_id=cupom.id, user_id=user_id, pedido_id=pedido_id))
            session.commit()

    def estornar_uso(self, pedido_id: str) -> None:
        with create_session() as session:
            usos = session.exec(
                select(CupomUsoModel).where(CupomUsoModel.pedido_id == pedido_id)
            ).all()
            for uso in usos:
                session.delete(uso)
            session.commit()

    @staticmethod
    def _validar_limites(session, cupom_id: int, user_id: str) -> None:
        cupom = session.get(CupomModel, cupom_id)
        if cupom is None or not cupom.ativo:
            raise UsoCupomIndisponivelError("Cupom indisponivel")
        if cupom.limite_usos is not None:
            total = session.exec(
                select(func.count()).select_from(CupomUsoModel).where(CupomUsoModel.cupom_id == cupom_id)
            ).one()
            if total >= cupom.limite_usos:
                raise UsoCupomIndisponivelError("Limite total de usos do cupom atingido")
        if cupom.limite_por_usuario is not None:
            total_usuario = session.exec(
                select(func.count()).select_from(CupomUsoModel).where(
                    CupomUsoModel.cupom_id == cupom_id,
                    CupomUsoModel.user_id == user_id,
                )
            ).one()
            if total_usuario >= cupom.limite_por_usuario:
                raise UsoCupomIndisponivelError("Limite de uso do cupom por usuario atingido")
        if cupom.somente_novos_clientes:
            pagamento = session.exec(
                select(PaymentModel.id).where(
                    PaymentModel.user_id == user_id,
                    PaymentModel.status == PaymentStatus.aprovado,
                ).limit(1)
            ).first()
            if pagamento is not None:
                raise UsoCupomIndisponivelError("Cupom exclusivo para novos clientes")

    @staticmethod
    def _para_modelo(cupom: Cupom) -> CupomModel:
        return CupomModel(
            id=cupom.id,
            codigo=cupom.codigo,
            descricao=cupom.descricao,
            tipo=cupom.tipo.value,
            valor=cupom.valor,
            subtotal_minimo=cupom.subtotal_minimo,
            desconto_maximo=cupom.desconto_maximo,
            valido_de=cupom.valido_de,
            valido_ate=cupom.valido_ate,
            ativo=cupom.ativo,
            limite_usos=cupom.limite_usos,
            limite_por_usuario=cupom.limite_por_usuario,
            somente_novos_clientes=cupom.somente_novos_clientes,
        )

    @staticmethod
    def _para_entidade(modelo: CupomModel) -> Cupom:
        return Cupom(
            id=modelo.id,
            codigo=modelo.codigo,
            descricao=modelo.descricao,
            tipo=modelo.tipo,
            valor=modelo.valor,
            subtotal_minimo=modelo.subtotal_minimo,
            desconto_maximo=modelo.desconto_maximo,
            valido_de=modelo.valido_de,
            valido_ate=modelo.valido_ate,
            ativo=modelo.ativo,
            limite_usos=modelo.limite_usos,
            limite_por_usuario=modelo.limite_por_usuario,
            somente_novos_clientes=modelo.somente_novos_clientes,
        )

    @staticmethod
    def _copiar_para_modelo(cupom: Cupom, modelo: CupomModel) -> None:
        modelo.codigo = cupom.codigo
        modelo.descricao = cupom.descricao
        modelo.tipo = cupom.tipo.value
        modelo.valor = cupom.valor
        modelo.subtotal_minimo = cupom.subtotal_minimo
        modelo.desconto_maximo = cupom.desconto_maximo
        modelo.valido_de = cupom.valido_de
        modelo.valido_ate = cupom.valido_ate
        modelo.ativo = cupom.ativo
        modelo.limite_usos = cupom.limite_usos
        modelo.limite_por_usuario = cupom.limite_por_usuario
        modelo.somente_novos_clientes = cupom.somente_novos_clientes
