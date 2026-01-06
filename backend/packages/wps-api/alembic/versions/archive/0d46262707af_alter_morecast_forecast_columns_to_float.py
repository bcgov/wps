"""Alter morecast_forecast columns to float

Revision ID: 0d46262707af
Revises: 69cbd7ca2477
Create Date: 2023-03-14 15:55:31.325373

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d46262707af'
down_revision = '69cbd7ca2477'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('morecast_forecast', 'temp')
    op.drop_column('morecast_forecast', 'precip')
    op.drop_column('morecast_forecast', 'wind_speed')
    op.add_column('morecast_forecast', sa.Column('temp', sa.Float(), nullable=False))
    op.add_column('morecast_forecast', sa.Column('precip', sa.Float(), nullable=False))
    op.add_column('morecast_forecast', sa.Column('wind_speed', sa.Float(), nullable=False))


def downgrade():
    op.drop_column('morecast_forecast', 'temp')
    op.drop_column('morecast_forecast', 'precip')
    op.drop_column('morecast_forecast', 'wind_speed')
    op.add_column('morecast_forecast', sa.Column('temp', sa.Integer(), nullable=False))
    op.add_column('morecast_forecast', sa.Column('precip', sa.Integer(), nullable=False))
    op.add_column('morecast_forecast', sa.Column('wind_speed', sa.Integer(), nullable=False))
