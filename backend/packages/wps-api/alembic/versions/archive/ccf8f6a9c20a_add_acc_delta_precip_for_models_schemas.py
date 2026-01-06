"""add acc. & delta precip for models schemas

Revision ID: ccf8f6a9c20a
Revises: e55ea62e7ec1
Create Date: 2020-11-25 14:48:08.117200

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ccf8f6a9c20a'
down_revision = 'e55ea62e7ec1'
branch_labels = None
depends_on = None


def upgrade():
    # Add accumulated precipitation columns to model_run_grid_subset_predictions and
    # weather_station_model_predictions schemas. Add delta_precip column to
    # weather_station_model_predictions schema ###
    op.add_column('model_run_grid_subset_predictions', sa.Column(
        'apcp_sfc_0', postgresql.ARRAY(sa.Float()), nullable=True))
    op.add_column('weather_station_model_predictions',
                  sa.Column('apcp_sfc_0', sa.Float(), nullable=True))
    op.add_column('weather_station_model_predictions', sa.Column(
        'delta_precip', sa.Float(), nullable=True))


def downgrade():
    # Drop the precipitation-related columns from weather_station_model_predictions
    # and model_run_grid_subset_predictions schemas ###
    op.drop_column('weather_station_model_predictions', 'delta_precip')
    op.drop_column('weather_station_model_predictions', 'apcp_sfc_0')
    op.drop_column('model_run_grid_subset_predictions', 'apcp_sfc_0')
