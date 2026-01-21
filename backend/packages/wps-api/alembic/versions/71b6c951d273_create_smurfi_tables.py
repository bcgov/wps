"""create_smurfi_tables

Revision ID: 71b6c951d273
Revises: cf8397b26783
Create Date: 2026-01-21 10:39:43.315678

"""
from venv import create
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '71b6c951d273'
down_revision = 'cf8397b26783'
branch_labels = None
depends_on = None



def upgrade():

    frequency_enum = sa.Enum(
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
    name='frequency_day_enum'
    )

    request_type_enum = sa.Enum(
        'Full', 'Mini', 'Ventilation', name='request_type_enum'
    )

    spot_status_enum = sa.Enum(
        'Requested', 'Started', 'Suspended', 'Complete', 'Archived', name='spot_request_status_enum'
    )

    period_enum = sa.Enum(
        'Today', 'Tonight', 'Tomorrow', name='spot_forecast_period_enum'
    )
    

    op.create_table(
        "spot_request",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("fire_number", sa.String(), nullable=False),
        sa.Column("request_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", spot_status_enum, nullable=False),
        sa.Column('requested_frequency', sa.ARRAY(frequency_enum), nullable=True),
        sa.Column('requested_type', request_type_enum, nullable=False),
        sa.Column("additional_info", sa.Text(), nullable=True),
        sa.Column("requested_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        comment="Requests for SMURFI spot forecasts"
    )
    op.create_index(
        op.f("ix_spot_request_fire_number"),
        "spot_request",
        ["fire_number"],
        unique=False,
    )
    op.create_table(
        "spot_request_audit",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("spot_request_id", sa.Integer(), sa.ForeignKey("spot_request.id"), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("changed_by", sa.String(), nullable=False),
        comment="Audit trail for changes to SMURFI spot requests"
    )

    op.create_table(
        "spot",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("spot_request_id", sa.Integer(), sa.ForeignKey("spot_request.id"), nullable=False),
        sa.Column("original_forecaster", sa.String(), nullable=False),
        sa.Column("forecaster_email", sa.String(), nullable=False), # not sure if this field is required. Email might always be the same general email or could be moved to a contact table
        sa.Column("forecaster_phone", sa.String(), nullable=True), # not sure if this field is required. Phone might always be the same general number or could be moved to a contact table
        sa.Column("geographic_area_name", sa.String(), nullable=False),
        sa.Column("representative_weather_stations", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("fire_centre", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        comment="SMURFI spot forecasts"
    )
    op.create_index(
        op.f("ix_spot_spot_request_id"),
        "spot",
        ["spot_request_id"],
        unique=False,
    )
    op.create_table(
        "spot_audit",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("spot_id", sa.Integer(), sa.ForeignKey("spot.id"), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("changed_by", sa.String(), nullable=False),
        comment="Audit trail for changes to SMURFI spots"
    )

    op.create_table(
        "spot_version",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("spot_id", sa.Integer(), sa.ForeignKey("spot.id"), nullable=False),
        sa.Column("primary_fire_number", sa.String(), nullable=False),
        sa.Column("additional_fire_numbers", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("forecaster", sa.String(), nullable=False),
        sa.Column("forecaster_email", sa.String(), nullable=True),
        sa.Column("forecaster_phone", sa.String(), nullable=True),
        sa.Column("representative_weather_stations", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("elevation", sa.Float(), nullable=True),
        sa.Column("valley", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        comment="Versions of SMURFI spot forecasts"
    )
    op.create_index(
        op.f("ix_spot_version_spot_id"),
        "spot_version",
        ["spot_id"],
        unique=False,
    )
    op.create_table(
        "spot_version_audit",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("spot_version_id", sa.Integer(), sa.ForeignKey("spot_version.id"), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("changed_by", sa.String(), nullable=False),
        comment="Audit trail for changes to SMURFI spot versions"
    )

    op.create_table(
        "spot_forecast",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("spot_version_id", sa.Integer(), sa.ForeignKey("spot_version.id"), nullable=False),
        sa.Column("forecast_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("relative_humidity", sa.Float(), nullable=True),
        sa.Column("wind", sa.String(), nullable=True),
        sa.Column("probability_of_precipitation", sa.Float(), nullable=True),
        sa.Column("precipitation_amount", sa.Float(), nullable=True),
        comment="SMURFI spot detailed forecasts representing a specific time period"
    )
    op.create_index(
        op.f("ix_spot_forecast_spot_version_id"),
        "spot_forecast",
        ["spot_version_id"],
        unique=False,
    )

    op.create_table(
        "spot_general_forecast",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("spot_version_id", sa.Integer(), sa.ForeignKey("spot_version.id"), nullable=False),
        sa.Column("period", period_enum, nullable=False),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("relative_humidity", sa.Float(), nullable=True),
        sa.Column("conditions", sa.String(), nullable=True),
        comment="SMURFI spot general(less detailed) forecasts representing a broad time period"
    )
    op.create_index(
        op.f("ix_spot_general_forecast_spot_version_id"),
        "spot_general_forecast",
        ["spot_version_id"],
        unique=False,
    )


def downgrade():
    op.drop_table("spot_general_forecast")
    op.drop_table("spot_forecast")
    op.drop_table("spot_version")
    op.drop_table("spot")
    op.drop_table("spot_request_audit")
    op.drop_table("spot_request")

    period_enum = sa.Enum(
        'Today', 'Tonight', 'Tomorrow', name='spot_forecast_period_enum'
    )
    period_enum.drop(op.get_bind(), checkfirst=True)
    spot_status_enum = sa.Enum(
        'Requested', 'Started', 'Suspended', 'Complete', 'Archived', name='spot_request_status_enum'
    )
    spot_status_enum.drop(op.get_bind(), checkfirst=True)
    request_type_enum = sa.Enum(
        'Full', 'Mini', 'Ventilation', name='request_type_enum'
    )
    request_type_enum.drop(op.get_bind(), checkfirst=True)
    frequency_enum = sa.Enum(
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
    name='frequency_day_enum'
    )
    frequency_enum.drop(op.get_bind(), checkfirst=True) 
