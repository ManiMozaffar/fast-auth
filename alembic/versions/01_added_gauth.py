"""added: gauth

Revision ID: 9017c3813154
Revises: 5f60e74e0fe3
Create Date: 2023-07-09 13:04:17.895709

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9017c3813154"
down_revision = "5f60e74e0fe3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("users", sa.Column("gauth", sa.String(), nullable=False))
    op.create_unique_constraint(None, "users", ["id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "users", type_="unique")
    op.drop_column("users", "gauth")
    # ### end Alembic commands ###
