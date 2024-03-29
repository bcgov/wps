"""Allows null dewpoint values for hourly actuals

Revision ID: 4ac7d9f38f85
Revises: aa82757b1084
Create Date: 2021-06-01 14:29:49.951368

"""
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4ac7d9f38f85'
down_revision = 'aa82757b1084'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('hourly_actuals', 'dewpoint',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('hourly_actuals', 'dewpoint',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=False)
    # ### end Alembic commands ###
