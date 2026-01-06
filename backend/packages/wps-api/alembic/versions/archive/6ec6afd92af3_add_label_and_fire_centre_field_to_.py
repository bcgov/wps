"""Add label and fire centre field to advisory_shapes

Revision ID: 6ec6afd92af3
Revises: 2b3755392ad8
Create Date: 2024-04-30 10:22:37.880294

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "6ec6afd92af3"
down_revision = "2b3755392ad8"
branch_labels = None
depends_on = None


def upgrade():
    # ### start Alembic commands ###
    op.add_column("advisory_shapes", sa.Column("label", sa.String(), nullable=True))
    op.add_column("advisory_shapes", sa.Column("fire_centre", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_advisory_shapes_fire_centre"), "advisory_shapes", ["fire_centre"], unique=False)
    op.create_foreign_key("advisory_shapes_fire_centres_fkey", "advisory_shapes", "fire_centres", ["fire_centre"], ["id"])
    # ### end Alembic commands ###


def downgrade():
    # ### start Alembic commands ###
    op.drop_constraint("advisory_shapes_fire_centres_fkey", "advisory_shapes", type_="foreignkey")
    op.drop_index(op.f("ix_advisory_shapes_fire_centre"), table_name="advisory_shapes")
    op.drop_column("advisory_shapes", "fire_centre")
    op.drop_column("advisory_shapes", "label")
    # ### end Alembic commands ###
