"""fix KFC prep levels

Revision ID: cbde211a0c72
Revises: 6f7d3e9c2a10
Create Date: 2026-07-06 10:38:25.198998

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cbde211a0c72"
down_revision = "6f7d3e9c2a10"
branch_labels = None
depends_on = None


def upgrade():
    # https://github.com/bcgov/wps/issues/5575
    op.execute("""
        UPDATE hfi_fire_start_lookup
        SET prep_level = 3
        WHERE fire_start_range_id = (SELECT id FROM hfi_fire_start_range WHERE label = '1-2')
        AND mean_intensity_group = 3
    """)

    op.execute("""
        UPDATE hfi_fire_start_lookup
        SET prep_level = 5
        WHERE fire_start_range_id = (SELECT id FROM hfi_fire_start_range WHERE label = '3-6')
        AND mean_intensity_group = 3
    """)

    op.execute("""
        UPDATE hfi_fire_start_lookup
        SET prep_level = 6
        WHERE fire_start_range_id = (SELECT id FROM hfi_fire_start_range WHERE label = '3-6')
        AND mean_intensity_group = 4
    """)


def downgrade():
    op.execute("""
        UPDATE hfi_fire_start_lookup
        SET prep_level = 2
        WHERE fire_start_range_id = (SELECT id FROM hfi_fire_start_range WHERE label = '1-2')
        AND mean_intensity_group = 3
    """)

    op.execute("""
        UPDATE hfi_fire_start_lookup
        SET prep_level = 4
        WHERE fire_start_range_id = (SELECT id FROM hfi_fire_start_range WHERE label = '3-6')
        AND mean_intensity_group = 3
    """)

    op.execute("""
        UPDATE hfi_fire_start_lookup
        SET prep_level = 5
        WHERE fire_start_range_id = (SELECT id FROM hfi_fire_start_range WHERE label = '3-6')
        AND mean_intensity_group = 4
    """)
