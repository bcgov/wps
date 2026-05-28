"""Adjust prep level for KFC

Revision ID: d3513840fd37
Revises: 0f0c47b0c47a
Create Date: 2026-05-28 09:58:15.454075

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd3513840fd37'
down_revision = '0f0c47b0c47a'
branch_labels = None
depends_on = None


def upgrade():
    # https://github.com/bcgov/wps/issues/5432
    op.execute("""
        UPDATE hfi_fire_start_lookup
        SET prep_level = 2
        WHERE fire_start_range_id = (SELECT id FROM hfi_fire_start_range WHERE label = '1-2')
        AND mean_intensity_group = 2
    """)


def downgrade():
    op.execute("""
        UPDATE hfi_fire_start_lookup
        SET prep_level = 1
        WHERE fire_start_range_id = (SELECT id FROM hfi_fire_start_range WHERE label = '1-2')
        AND mean_intensity_group = 2
    """)
