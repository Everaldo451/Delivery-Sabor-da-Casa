import sqlalchemy as sa
from alembic import op

revision = "20261122_06"
down_revision = "20261121_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "favoritos",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("prato_id", sa.String(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["prato_id"], ["pratos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "prato_id"),
    )

    op.create_table(
        "cupons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("codigo", sa.String(length=30), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "subtotal_minimo",
            sa.Numeric(10, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("desconto_maximo", sa.Numeric(10, 2), nullable=True),
        sa.Column("limite_usos", sa.Integer(), nullable=True),
        sa.Column("limite_por_usuario", sa.Integer(), server_default="1", nullable=True),
        sa.Column("somente_novos_clientes", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("valido_de", sa.Date(), nullable=True),
        sa.Column("valido_ate", sa.Date(), nullable=True),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cupons_codigo", "cupons", ["codigo"], unique=True)

    op.create_table(
        "usos_cupom",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cupom_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("pedido_id", sa.String(length=100), nullable=False),
        sa.Column("usado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["cupom_id"], ["cupons.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cupom_id", "pedido_id", name="uq_usos_cupom_pedido"),
    )
    op.create_index("ix_usos_cupom_cupom_id", "usos_cupom", ["cupom_id"])
    op.create_index("ix_usos_cupom_user_id", "usos_cupom", ["user_id"])
    op.create_index("ix_usos_cupom_pedido_id", "usos_cupom", ["pedido_id"])

    op.create_table(
        "transacoes_fidelidade",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("pedido_id", sa.String(length=100), nullable=True),
        sa.Column("pontos", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "pedido_id",
            "tipo",
            name="uq_transacoes_fidelidade_pedido_tipo",
        ),
    )
    op.create_index(
        "ix_transacoes_fidelidade_user_id",
        "transacoes_fidelidade",
        ["user_id"],
    )
    op.create_index(
        "ix_transacoes_fidelidade_pedido_id",
        "transacoes_fidelidade",
        ["pedido_id"],
    )
    op.create_index(
        "ix_transacoes_fidelidade_tipo",
        "transacoes_fidelidade",
        ["tipo"],
    )


def downgrade() -> None:
    op.drop_index("ix_usos_cupom_pedido_id", table_name="usos_cupom")
    op.drop_index("ix_usos_cupom_user_id", table_name="usos_cupom")
    op.drop_index("ix_usos_cupom_cupom_id", table_name="usos_cupom")
    op.drop_table("usos_cupom")
    op.drop_index("ix_transacoes_fidelidade_tipo", table_name="transacoes_fidelidade")
    op.drop_index("ix_transacoes_fidelidade_pedido_id", table_name="transacoes_fidelidade")
    op.drop_index("ix_transacoes_fidelidade_user_id", table_name="transacoes_fidelidade")
    op.drop_table("transacoes_fidelidade")
    op.drop_index("ix_cupons_codigo", table_name="cupons")
    op.drop_table("cupons")
    op.drop_table("favoritos")
