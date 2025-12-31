"""adds grass_curing to morecast_forecast

Revision ID: 5845f568a975
Revises: 403586c146ae
Create Date: 2024-02-02 08:16:57.605162

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5845f568a975'
down_revision = '403586c146ae'
branch_labels = None
depends_on = None


def upgrade():
    # ### start Alembic commands ###
    op.add_column('morecast_forecast', sa.Column('grass_curing', sa.Float(), nullable=True))
    op.create_index(op.f('ix_morecast_forecast_grass_curing'), 'morecast_forecast', ['grass_curing'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### start Alembic commands ###
    op.drop_index(op.f('ix_morecast_forecast_grass_curing'), table_name='morecast_forecast')
    op.drop_column('morecast_forecast', 'grass_curing')
    # ### end Alembic commands ###
