"""rdps_latlon_projection

Revision ID: 05349c55c1e2
Revises: 591bf3e24705
Create Date: 2026-04-14 16:16:51.902177

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '05349c55c1e2'
down_revision = '591bf3e24705'
branch_labels = None
depends_on = None


def upgrade():
    # Adds the new MSC RLatLon0.09 RDPS row alongside the legacy ps10km row.
    # Both rows coexist during the S3 retention window (DAYS_TO_RETAIN = 7 in rdps_sfms.py)
    # while legacy-format keys age out. The legacy ps10km row should be retired in a
    # follow-up migration once old-format data is fully purged.
    # The seed migration inserts prediction_models rows with explicit ids, which don't advance the
    # sequence. Reset it so subsequent inserts without an explicit id don't collide.
    op.execute("SELECT setval(pg_get_serial_sequence('prediction_models', 'id'), MAX(id)) FROM prediction_models")
    op.execute(
        "INSERT INTO prediction_models (abbreviation, name, projection) "
        "VALUES ('RDPS', 'Regional Deterministic Prediction System', 'RLatLon0.09')"
    )


def downgrade():
    op.execute(
        "DELETE FROM prediction_models WHERE abbreviation = 'RDPS' AND projection = 'RLatLon0.09'"
    )
