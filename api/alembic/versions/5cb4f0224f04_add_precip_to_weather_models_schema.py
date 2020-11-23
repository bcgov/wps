"""add precip to weather_models schema

Revision ID: 5cb4f0224f04
Revises: e55ea62e7ec1
Create Date: 2020-11-23 11:21:17.476240

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5cb4f0224f04'
down_revision = 'e55ea62e7ec1'
branch_labels = None
depends_on = None


def upgrade():
    ### Add acculumated precipitation (apcp_sfc_0) columns to model predictions schemas ###
    op.add_column('model_run_grid_subset_predictions', sa.Column(
        'apcp_sfc_0', postgresql.ARRAY(sa.Float()), nullable=True))
    op.add_column('weather_station_model_predictions',
                  sa.Column('apcp_sfc_0', sa.Float(), nullable=True))


def downgrade():
    ### Drop accumulated precipitation (apcp_sfc_0) columns from model predictions schemas ###
    op.drop_column('weather_station_model_predictions', 'apcp_sfc_0')
    op.drop_column('model_run_grid_subset_predictions', 'apcp_sfc_0')
