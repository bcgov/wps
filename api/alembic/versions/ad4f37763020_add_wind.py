"""Add wind

Revision ID: ad4f37763020
Revises: ccf8f6a9c20a
Create Date: 2020-12-24 10:36:45.172752

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ad4f37763020'
down_revision = 'ccf8f6a9c20a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('model_run_grid_subset_predictions', sa.Column(
        'wdir_tgl_10', postgresql.ARRAY(sa.Float()), nullable=True))
    op.add_column('model_run_grid_subset_predictions', sa.Column(
        'wind_tgl_10', postgresql.ARRAY(sa.Float()), nullable=True))
    op.add_column('weather_station_model_predictions', sa.Column('wdir_tgl_10', sa.Float(), nullable=True))
    op.add_column('weather_station_model_predictions', sa.Column('wind_tgl_10', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('weather_station_model_predictions', 'wind_tgl_10')
    op.drop_column('weather_station_model_predictions', 'wdir_tgl_10')
    op.drop_column('model_run_grid_subset_predictions', 'wind_tgl_10')
    op.drop_column('model_run_grid_subset_predictions', 'wdir_tgl_10')
