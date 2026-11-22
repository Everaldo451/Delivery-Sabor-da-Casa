import sqlalchemy as sa
from alembic import op

revision = "20261121_03"
down_revision = "20261121_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categorias",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categorias_nome", "categorias", ["nome"], unique=True)
    op.bulk_insert(
        sa.table("categorias", sa.column("nome", sa.String(length=80))),
        [
            {"nome": "Pratos"},
            {"nome": "Bebidas"},
            {"nome": "Sobremesas"},
        ],
    )

    op.create_table(
        "pratos",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("preco", sa.Numeric(10, 2), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("imagem_url", sa.String(length=2048), nullable=True),
        sa.Column("disponivel", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categorias.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pratos_nome", "pratos", ["nome"])
    op.create_index("ix_pratos_categoria_id", "pratos", ["categoria_id"])
    op.create_index("ix_pratos_disponivel", "pratos", ["disponivel"])


def downgrade() -> None:
    op.drop_index("ix_pratos_disponivel", table_name="pratos")
    op.drop_index("ix_pratos_categoria_id", table_name="pratos")
    op.drop_index("ix_pratos_nome", table_name="pratos")
    op.drop_table("pratos")
    op.drop_index("ix_categorias_nome", table_name="categorias")
    op.drop_table("categorias")
