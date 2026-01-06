"""seed_application_data

Revision ID: 6157a8d08f28
Revises: 9bb0dc8ed7fb
Create Date: 2025-12-29 14:44:23.524448

"""

from alembic import op
import sqlalchemy as sa
from pathlib import Path
import re
import gzip
from shapely import wkb


# revision identifiers, used by Alembic.
revision = "6157a8d08f28"
down_revision = "9bb0dc8ed7fb"
branch_labels = None
depends_on = None


def transform_geometry_values(statement: str) -> str:
    """Transform PostGIS geometry hex strings to use ST_GeomFromEWKB() with decode()

    Uses shapely to validate that hex strings are actually valid WKB geometry data
    before transforming them.
    """
    # Pattern to match hex strings that look like PostGIS EWKB format
    pattern = r"'(01[0-9A-Fa-f]{8,})'"

    def replace_hex(match: re.Match[str]) -> str:
        hex_string = match.group(1)
        try:
            # Use shapely to validate this is actually WKB geometry data
            wkb.loads(bytes.fromhex(hex_string))
            # If valid, wrap in ST_GeomFromEWKB with decode() to avoid asyncpg parsing
            return f"ST_GeomFromEWKB(decode('{hex_string}', 'hex'))"
        except Exception:
            # Not valid WKB geometry, return original
            return match.group(0)

    return re.sub(pattern, replace_hex, statement)


def upgrade():
    """Load application data from SQL file"""
    # Path to the data file (relative to this migration file)
    migration_dir = Path(__file__).parent.parent
    data_file = migration_dir / "data" / "application_seed_data.sql.gz"

    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")

    # Get the connection without prepared statements to avoid asyncpg geometry parsing
    connection = op.get_bind().execution_options(prepared=False)

    # Execute each INSERT statement individually
    with gzip.open(data_file, "rt") as f:
        statement_buffer = []

        for line in f:
            # Skip comments and empty lines
            if line.strip().startswith("--") or not line.strip():
                continue

            statement_buffer.append(line)

            # Execute when we hit a semicolon (end of statement)
            if line.strip().endswith(";"):
                statement = "".join(statement_buffer).strip()
                if statement.startswith("INSERT"):
                    # Transform geometry hex strings to PostGIS function calls
                    transformed = transform_geometry_values(statement)
                    connection.execute(sa.text(transformed))
                statement_buffer = []


def downgrade():
    """Remove seeded application data"""
    # Delete data from the 18 application tables in reverse dependency order
    op.execute("DELETE FROM advisory_shape_fuels;")
    op.execute("DELETE FROM advisory_fuel_types;")
    op.execute("DELETE FROM tpi_fuel_area;")
    op.execute("DELETE FROM combustible_area;")
    op.execute("DELETE FROM advisory_shapes;")
    op.execute("DELETE FROM advisory_shape_types;")
    op.execute("DELETE FROM advisory_hfi_classification_threshold;")
    op.execute("DELETE FROM hfi_fire_centre_fire_start_range;")
    op.execute("DELETE FROM hfi_fire_start_lookup;")
    op.execute("DELETE FROM hfi_fire_start_range;")
    op.execute("DELETE FROM planning_weather_stations;")
    op.execute("DELETE FROM planning_areas;")
    op.execute("DELETE FROM fire_centres;")
    op.execute("DELETE FROM fuel_type_raster;")
    op.execute("DELETE FROM sfms_fuel_types;")
    op.execute("DELETE FROM fuel_types;")
    op.execute("DELETE FROM prescription_status;")
    op.execute("DELETE FROM prediction_models;")
