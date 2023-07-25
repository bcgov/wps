"""Add 24 hour precip field to WeatherStationModelPrediction

Revision ID: 7217281a3218
Revises: 4916cd5313de
Create Date: 2023-07-25 10:53:19.447483

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7217281a3218'
down_revision = '4916cd5313de'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('weather_station_model_predictions', sa.Column('precip_24h', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('weather_station_model_predictions', 'precip_24h')
