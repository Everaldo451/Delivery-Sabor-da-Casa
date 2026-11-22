import sqlalchemy as sa
from alembic import op

revision = "20261121_05"
down_revision = "20261121_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("pratos", "imagem_url")


def downgrade() -> None:
    op.add_column(
        "pratos",
        sa.Column("imagem_url", sa.String(length=2048), nullable=True),
    )
