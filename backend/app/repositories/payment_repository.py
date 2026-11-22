from sqlmodel import select

from app.database.postgresql import create_session
from app.database.postgresql.models.payment import PaymentModel
from app.entities.payment import Payment


class PaymentRepository:
    def _para_entidade(self, payment_model: PaymentModel) -> Payment:
        return Payment.model_validate(payment_model.model_dump())

    def _para_modelo(self, payment: Payment) -> PaymentModel:
        return PaymentModel(
            id=payment.id,
            pedido_id=payment.pedido_id,
            user_id=payment.user_id,
            amount=payment.amount,
            method=payment.method,
            status=payment.status,
            simulation_result=payment.simulation_result,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )

    def inserir(self, payment: Payment) -> Payment:
        payment_model = self._para_modelo(payment)
        with create_session() as session:
            session.add(payment_model)
            session.commit()
            session.refresh(payment_model)
            return self._para_entidade(payment_model)

    def buscar_por_id(self, payment_id: int) -> Payment | None:
        with create_session() as session:
            payment_model = session.get(PaymentModel, payment_id)
            return (
                self._para_entidade(payment_model)
                if payment_model is not None
                else None
            )

    def listar_por_usuario(self, user_id: str) -> list[Payment]:
        with create_session() as session:
            statement = (
                select(PaymentModel)
                .where(PaymentModel.user_id == user_id)
                .order_by(PaymentModel.created_at.desc())
            )
            payment_models = session.exec(statement).all()
            return [
                self._para_entidade(payment_model)
                for payment_model in payment_models
            ]
