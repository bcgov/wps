"""SMURFI models

Revision ID: f5bb9e85fd0a
Revises: 0f0c47b0c47a
Create Date: 2026-05-19 08:52:27.220394

"""
import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql
from wps_shared.db.models.common import TZTimeStamp

# revision identifiers, used by Alembic.
revision = 'f5bb9e85fd0a'
down_revision = '0f0c47b0c47a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('spot_request',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('request_reference', sa.String(), nullable=False),
    sa.Column('fire_number', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('fire_centre', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('requestor_name', sa.String(), nullable=False),
    sa.Column('requestor_idir', sa.String(), nullable=False),
    sa.Column('requestor_email', sa.String(), nullable=False),
    sa.Column('request_frequency', sa.ARRAY(sa.Enum('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', name='frequencydayenum')), nullable=True),
    sa.Column('request_type', sa.String(), nullable=False),
    sa.Column('aspect', sa.String(), nullable=True),
    sa.Column('elevation', sa.Integer(), nullable=True),
    sa.Column('geographic_description', sa.String(), nullable=False),
    sa.Column('geom', Geometry(geometry_type='POINT', srid=3005, dimension=2, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.Column('representative_station_codes', sa.ARRAY(sa.Integer()), nullable=True),
    sa.Column('requested_at', TZTimeStamp(), nullable=False),
    sa.Column('start_at', TZTimeStamp(), nullable=False),
    sa.Column('end_at', TZTimeStamp(), nullable=False),
    sa.Column('created_at', TZTimeStamp(), nullable=False),
    sa.Column('updated_at', TZTimeStamp(), nullable=False),
    sa.CheckConstraint("aspect IN ('North', 'Northwest', 'West', 'Southwest', 'South', 'Southeast', 'East', 'Northeast')", name='chk_aspect_spot_request'),
    sa.CheckConstraint("request_type IN ('Full', 'Mini')", name='chk_request_type_spot_request'),
    sa.CheckConstraint("status IN ('Requested', 'Started', 'Suspended', 'Complete', 'Archived')", name='chk_status_spot_request'),
    sa.ForeignKeyConstraint(['fire_centre'], ['fire_centres.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='Tracks requests for spot weather forecasts.'
    )
    op.create_index(op.f('ix_spot_request_end_at'), 'spot_request', ['end_at'], unique=False)
    op.create_index(op.f('ix_spot_request_start_at'), 'spot_request', ['start_at'], unique=False)
    op.create_index(op.f('ix_spot_request_status'), 'spot_request', ['status'], unique=False)
    op.create_table('spot_forecast',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('spot_request_id', sa.Integer(), nullable=False),
    sa.Column('forecaster_name', sa.String(), nullable=False),
    sa.Column('forecaster_email', sa.String(), nullable=False),
    sa.Column('forecaster_phone', sa.String(), nullable=True),
    sa.Column('synopsis', sa.Text(), nullable=True),
    sa.Column('inversion_and_venting', sa.Text(), nullable=True),
    sa.Column('outlook', sa.Text(), nullable=True),
    sa.Column('confidence', sa.Text(), nullable=True),
    sa.Column('fire_size', sa.Float(), nullable=True),
    sa.Column('created_at', TZTimeStamp(), nullable=False),
    sa.Column('updated_at', TZTimeStamp(), nullable=True),
    sa.ForeignKeyConstraint(['spot_request_id'], ['spot_request.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='Spot forecasts for spot requests.'
    )
    op.create_index(op.f('ix_spot_forecast_forecaster_name'), 'spot_forecast', ['forecaster_name'], unique=False)
    op.create_index(op.f('ix_spot_forecast_spot_request_id'), 'spot_forecast', ['spot_request_id'], unique=False)
    op.create_table('spot_subscriber',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('spot_request_id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('subscriber_status', sa.String(), nullable=False),
    sa.Column('created_at', TZTimeStamp(), nullable=False),
    sa.Column('updated_at', TZTimeStamp(), nullable=False),
    sa.CheckConstraint("subscriber_status IN ('active', 'inactive')", name='chk_subscriber_status_spot_subscriber'),
    sa.ForeignKeyConstraint(['spot_request_id'], ['spot_request.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='Tracks email addresses subscribed to spot forecasts for a spot requests.'
    )
    op.create_index(op.f('ix_spot_subscriber_email'), 'spot_subscriber', ['email'], unique=False)
    op.create_index(op.f('ix_spot_subscriber_spot_request_id'), 'spot_subscriber', ['spot_request_id'], unique=False)
    op.create_table('spot_descriptive_weather',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('spot_forecast_id', sa.Integer(), nullable=False),
    sa.Column('period', sa.String(), nullable=False),
    sa.Column('temperature', sa.Float(), nullable=True),
    sa.Column('relative_humidity', sa.Float(), nullable=True),
    sa.Column('conditions', sa.String(), nullable=True),
    sa.CheckConstraint("period IN ('Today', 'Tonight', 'Tomorrow')", name='chk_period_spot_descriptive_weather'),
    sa.ForeignKeyConstraint(['spot_forecast_id'], ['spot_forecast.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='Represents a general text based forecast which includes a description of conditions, temperature and humidity. '
    )
    op.create_index(op.f('ix_spot_descriptive_weather_spot_forecast_id'), 'spot_descriptive_weather', ['spot_forecast_id'], unique=False)
    op.create_table('spot_tabular_weather',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('spot_forecast_id', sa.Integer(), nullable=False),
    sa.Column('forecast_time', TZTimeStamp(), nullable=False),
    sa.Column('temperature', sa.Float(), nullable=True),
    sa.Column('relative_humidity', sa.Float(), nullable=True),
    sa.Column('wind', sa.String(), nullable=True),
    sa.Column('probability_of_precipitation', sa.Float(), nullable=True),
    sa.Column('precipitation_amount', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['spot_forecast_id'], ['spot_forecast.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='Detailed numerical forecasts for weather variable in a spot forecast.'
    )
    op.create_index(op.f('ix_spot_tabular_weather_spot_forecast_id'), 'spot_tabular_weather', ['spot_forecast_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_spot_tabular_weather_spot_forecast_id'), table_name='spot_tabular_weather')
    op.drop_table('spot_tabular_weather')
    op.drop_index(op.f('ix_spot_descriptive_weather_spot_forecast_id'), table_name='spot_descriptive_weather')
    op.drop_table('spot_descriptive_weather')
    op.drop_index(op.f('ix_spot_subscriber_spot_request_id'), table_name='spot_subscriber')
    op.drop_index(op.f('ix_spot_subscriber_email'), table_name='spot_subscriber')
    op.drop_table('spot_subscriber')
    op.drop_index(op.f('ix_spot_forecast_spot_request_id'), table_name='spot_forecast')
    op.drop_index(op.f('ix_spot_forecast_forecaster_name'), table_name='spot_forecast')
    op.drop_table('spot_forecast')
    op.drop_index(op.f('ix_spot_request_status'), table_name='spot_request')
    op.drop_index(op.f('ix_spot_request_start_at'), table_name='spot_request')
    op.drop_index(op.f('ix_spot_request_end_at'), table_name='spot_request')
    op.drop_table('spot_request')
