"""weather station model prediction

Revision ID: c9f9b2849fef
Revises: 402cff253825
Create Date: 2020-09-03 13:21:00.206644

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9f9b2849fef'
down_revision = '402cff253825'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('weather_station_model_predictions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('station_code', sa.Integer(), nullable=False),
                    sa.Column('prediction_model_run_timestamp_id', sa.Integer(), nullable=False),
                    sa.Column('prediction_timestamp', sa.TIMESTAMP(
                        timezone=True), nullable=False),
                    sa.Column('tmp_tgl_2', sa.Float(), nullable=True),
                    sa.Column('rh_tgl_2', sa.Float(), nullable=True),
                    sa.Column('create_date', sa.TIMESTAMP(
                        timezone=True), nullable=False),
                    sa.Column('update_date', sa.TIMESTAMP(
                        timezone=True), nullable=False),
                    sa.ForeignKeyConstraint(['prediction_model_run_timestamp_id'], [
                        'prediction_model_run_timestamps.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('station_code', 'prediction_model_run_timestamp_id',
                                        'prediction_timestamp'),
                    comment='The interpolated weather values for a weather station, weather date, and model run'
                    )
    op.create_index(op.f('ix_weather_station_model_predictions_id'),
                    'weather_station_model_predictions', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_weather_station_model_predictions_id'),
                  table_name='weather_station_model_predictions')
    op.drop_table('weather_station_model_predictions')
