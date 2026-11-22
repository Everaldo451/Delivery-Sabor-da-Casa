from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.database.postgresql import create_session
from app.database.postgresql.models.fidelidade import TransacaoFidelidadeModel
from app.database.postgresql.models.user import UserModel
from app.entities.fidelidade import TransacaoFidelidade


class SaldoPontosInsuficienteError(Exception):
    pass


class FidelidadeRepository:
    TIPO_CREDITO_PEDIDO = "credito_pedido"
    TIPO_RESGATE_PEDIDO = "resgate_pedido"
    TIPO_ESTORNO_RESGATE = "estorno_resgate"

    def saldo(self, user_id: str) -> int:
        with create_session() as session:
            saldo = session.exec(
                select(func.coalesce(func.sum(TransacaoFidelidadeModel.pontos), 0))
                .where(TransacaoFidelidadeModel.user_id == user_id)
            ).one()
            return int(saldo)

    def listar_transacoes(self, user_id: str) -> list[TransacaoFidelidade]:
        with create_session() as session:
            transacoes = session.exec(
                select(TransacaoFidelidadeModel)
                .where(TransacaoFidelidadeModel.user_id == user_id)
                .order_by(TransacaoFidelidadeModel.criado_em.desc())
            ).all()
            return [self._para_entidade(transacao) for transacao in transacoes]

    def resgatar(self, user_id: str, pedido_id: str, pontos: int) -> int:
        with create_session() as session:
            self._bloquear_usuario(session, user_id)
            existente = session.exec(
                select(TransacaoFidelidadeModel).where(
                    TransacaoFidelidadeModel.pedido_id == pedido_id,
                    TransacaoFidelidadeModel.tipo == self.TIPO_RESGATE_PEDIDO,
                )
            ).first()
            if existente is not None:
                if existente.user_id != user_id or existente.pontos != -pontos:
                    raise SaldoPontosInsuficienteError(pedido_id)
                return self._saldo_na_sessao(session, user_id)

            saldo = self._saldo_na_sessao(session, user_id)
            if pontos > saldo:
                raise SaldoPontosInsuficienteError(user_id)

            session.add(
                TransacaoFidelidadeModel(
                    user_id=user_id,
                    pedido_id=pedido_id,
                    pontos=-pontos,
                    tipo=self.TIPO_RESGATE_PEDIDO,
                )
            )
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise SaldoPontosInsuficienteError(user_id) from exc
            return self._saldo_na_sessao(session, user_id)

    def creditar_por_pedido(
        self,
        user_id: str,
        pedido_id: str,
        pontos: int,
    ) -> int:
        if pontos <= 0:
            return self.saldo(user_id)
        with create_session() as session:
            self._bloquear_usuario(session, user_id)
            existente = session.exec(
                select(TransacaoFidelidadeModel).where(
                    TransacaoFidelidadeModel.pedido_id == pedido_id,
                    TransacaoFidelidadeModel.tipo == self.TIPO_CREDITO_PEDIDO,
                )
            ).first()
            if existente is None:
                session.add(
                    TransacaoFidelidadeModel(
                        user_id=user_id,
                        pedido_id=pedido_id,
                        pontos=pontos,
                        tipo=self.TIPO_CREDITO_PEDIDO,
                    )
                )
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()
            return self._saldo_na_sessao(session, user_id)

    def estornar_resgate(self, user_id: str, pedido_id: str) -> int:
        with create_session() as session:
            self._bloquear_usuario(session, user_id)
            resgate = session.exec(
                select(TransacaoFidelidadeModel).where(
                    TransacaoFidelidadeModel.user_id == user_id,
                    TransacaoFidelidadeModel.pedido_id == pedido_id,
                    TransacaoFidelidadeModel.tipo == self.TIPO_RESGATE_PEDIDO,
                )
            ).first()
            estorno = session.exec(
                select(TransacaoFidelidadeModel).where(
                    TransacaoFidelidadeModel.user_id == user_id,
                    TransacaoFidelidadeModel.pedido_id == pedido_id,
                    TransacaoFidelidadeModel.tipo == self.TIPO_ESTORNO_RESGATE,
                )
            ).first()
            if resgate is not None and estorno is None:
                session.add(
                    TransacaoFidelidadeModel(
                        user_id=user_id,
                        pedido_id=pedido_id,
                        pontos=-resgate.pontos,
                        tipo=self.TIPO_ESTORNO_RESGATE,
                    )
                )
                session.commit()
            return self._saldo_na_sessao(session, user_id)

    @staticmethod
    def _bloquear_usuario(session, user_id: str) -> None:
        usuario = session.exec(
            select(UserModel.id)
            .where(UserModel.id == user_id)
            .with_for_update()
        ).first()
        if usuario is None:
            raise LookupError(user_id)

    @staticmethod
    def _saldo_na_sessao(session, user_id: str) -> int:
        saldo = session.exec(
            select(func.coalesce(func.sum(TransacaoFidelidadeModel.pontos), 0))
            .where(TransacaoFidelidadeModel.user_id == user_id)
        ).one()
        return int(saldo)

    @staticmethod
    def _para_entidade(modelo: TransacaoFidelidadeModel) -> TransacaoFidelidade:
        return TransacaoFidelidade(
            id=modelo.id,
            user_id=modelo.user_id,
            pedido_id=modelo.pedido_id,
            pontos=modelo.pontos,
            tipo=modelo.tipo,
            criado_em=modelo.criado_em,
        )
