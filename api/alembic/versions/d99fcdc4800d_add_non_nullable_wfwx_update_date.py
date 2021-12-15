"""Add non-nullable wfwx update date

Revision ID: d99fcdc4800d
Revises: 1caf3488a340
Create Date: 2021-12-14 11:27:03.917981

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd99fcdc4800d'
down_revision = '1caf3488a340'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('noon_forecasts', sa.Column('wfwx_update_date', sa.TIMESTAMP(timezone=True), nullable=True))
    op.execute("UPDATE noon_forecasts SET wfwx_update_date = created_at")
    op.alter_column('noon_forecasts', 'wfwx_update_date', nullable=False)
    op.create_index(op.f('ix_noon_forecasts_wfwx_update_date'),
                    'noon_forecasts', ['wfwx_update_date'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_noon_forecasts_wfwx_update_date'), table_name='noon_forecasts')
    op.drop_column('noon_forecasts', 'wfwx_update_date')
