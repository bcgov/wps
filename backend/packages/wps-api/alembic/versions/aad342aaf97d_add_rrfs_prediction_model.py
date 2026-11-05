"""Add RRFS prediction model

Revision ID: aad342aaf97d
Revises: b7e3c1d9a4f2
Create Date: 2026-10-30 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "aad342aaf97d"
down_revision = "b7e3c1d9a4f2"
branch_labels = None
depends_on = None


def upgrade():
    # One row for the grid the RRFS job downloads by default (RRFS_GRID=na_13km). The job looks the
    # model up by abbreviation and projection, so switching to another grid needs a row for it too.
    op.execute(
        "INSERT INTO prediction_models (abbreviation, name, projection) "
        "VALUES ('RRFS', 'Rapid Refresh Forecast System', 'na.13km')"
    )


def downgrade():
    op.execute("DELETE FROM prediction_models WHERE abbreviation = 'RRFS' AND projection = 'na.13km'")
