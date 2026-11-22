import sqlalchemy as sa
from alembic import op

revision = "20261121_04"
down_revision = "20261121_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pratos",
        sa.Column("imagem_dados", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "pratos",
        sa.Column("imagem_content_type", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pratos", "imagem_content_type")
    op.drop_column("pratos", "imagem_dados")
