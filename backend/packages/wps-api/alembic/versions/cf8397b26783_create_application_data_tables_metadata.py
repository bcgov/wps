"""create_application_data_tables_metadata

Revision ID: cf8397b26783
Revises: 6157a8d08f28
Create Date: 2026-01-05 15:23:35.446768

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf8397b26783'
down_revision = '6157a8d08f28'
branch_labels = None
depends_on = None


def upgrade():
    # Create application_data_tables metadata table
    op.create_table(
        "application_data_tables",
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("seed_order", sa.Integer(), nullable=True),
        sa.Column("last_seeded", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("table_name"),
    )

    # Populate with metadata for the 18 application data tables
    connection = op.get_bind()
    connection.execute(
        sa.text("""
        INSERT INTO application_data_tables (table_name, description, seed_order, last_seeded) VALUES
        ('prediction_models', 'Prediction model definitions', 1, NOW()),
        ('fuel_types', 'Fuel type reference data', 2, NOW()),
        ('sfms_fuel_types', 'SFMS fuel type mappings', 3, NOW()),
        ('prescription_status', 'Prescription status types', 4, NOW()),
        ('fire_centres', 'Fire centre boundaries and definitions', 5, NOW()),
        ('planning_areas', 'Planning area definitions', 6, NOW()),
        ('advisory_hfi_classification_threshold', 'HFI classification thresholds', 7, NOW()),
        ('advisory_shape_types', 'Advisory shape type definitions', 8, NOW()),
        ('hfi_fire_start_range', 'HFI fire start range definitions', 9, NOW()),
        ('hfi_fire_start_lookup', 'HFI fire start lookup data', 10, NOW()),
        ('hfi_fire_centre_fire_start_range', 'HFI fire centre fire start ranges', 11, NOW()),
        ('fuel_type_raster', 'Fuel type raster metadata', 12, NOW()),
        ('planning_weather_stations', 'Planning weather station assignments', 13, NOW()),
        ('advisory_shapes', 'Advisory area shapes (fire zones, centres, units)', 14, NOW()),
        ('combustible_area', 'Combustible land area calculations', 15, NOW()),
        ('tpi_fuel_area', 'Topographic position index fuel area data', 16, NOW()),
        ('advisory_fuel_types', 'Fuel type distributions within advisory areas', 17, NOW()),
        ('advisory_shape_fuels', 'Advisory shape fuel type relationships', 18, NOW())
    """)
    )


def downgrade():
    op.drop_table("application_data_tables")
