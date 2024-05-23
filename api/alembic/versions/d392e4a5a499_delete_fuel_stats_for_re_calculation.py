"""Delete fuel stats for re-calculation

Revision ID: d392e4a5a499
Revises: c2cd7a585bbd
Create Date: 2024-05-23 09:39:44.787270

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd392e4a5a499'
down_revision = 'c2cd7a585bbd'
branch_labels = None
depends_on = None


def upgrade():
    stmt = """
            DELETE
            FROM
                advisory_fuel_stats afs
            WHERE
                afs.run_parameters in (
                SELECT
                    id
                FROM
                    run_parameters rp
                WHERE
                    rp.for_date >= '2024-05-01')
            """
    op.execute(stmt)


def downgrade():
    # No downgrade possible
    pass
