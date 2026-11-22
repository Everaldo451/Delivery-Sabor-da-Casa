import sqlalchemy as sa
from alembic import op

revision = "20261121_02"
down_revision = "20261121_01"
branch_labels = None
depends_on = None

FOREIGN_KEY_NAME = "fk_payments_user_id_users"


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    user_columns = {column["name"] for column in inspector.get_columns("users")}

    if "nome" not in user_columns:
        op.add_column(
            "users",
            sa.Column("nome", sa.String(length=120), nullable=True),
        )

    op.execute(sa.text("UPDATE users SET nome = '' WHERE nome IS NULL"))
    op.alter_column(
        "users",
        "nome",
        existing_type=sa.String(length=120),
        nullable=False,
    )

    payment_foreign_keys = inspector.get_foreign_keys("payments")
    matching_foreign_key = next(
        (
            foreign_key
            for foreign_key in payment_foreign_keys
            if foreign_key["constrained_columns"] == ["user_id"]
            and foreign_key["referred_table"] == "users"
            and foreign_key["referred_columns"] == ["id"]
        ),
        None,
    )
    if matching_foreign_key is None:
        orphan_count = connection.execute(
            sa.text(
                "SELECT COUNT(*) FROM payments AS payment "
                "WHERE NOT EXISTS ("
                "SELECT 1 FROM users AS app_user "
                "WHERE app_user.id = payment.user_id)"
            )
        ).scalar_one()
        if orphan_count:
            raise RuntimeError(
                "Nao foi possivel adicionar a FK de payments.user_id: "
                f"{orphan_count} pagamento(s) nao possuem usuario correspondente."
            )
        op.create_foreign_key(
            FOREIGN_KEY_NAME,
            "payments",
            "users",
            ["user_id"],
            ["id"],
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    matching_foreign_key = next(
        (
            foreign_key
            for foreign_key in inspector.get_foreign_keys("payments")
            if foreign_key["constrained_columns"] == ["user_id"]
            and foreign_key["referred_table"] == "users"
            and foreign_key["referred_columns"] == ["id"]
        ),
        None,
    )
    if matching_foreign_key is not None:
        op.drop_constraint(
            matching_foreign_key["name"],
            "payments",
            type_="foreignkey",
        )

    user_columns = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("users")
    }
    if "nome" in user_columns:
        op.drop_column("users", "nome")
