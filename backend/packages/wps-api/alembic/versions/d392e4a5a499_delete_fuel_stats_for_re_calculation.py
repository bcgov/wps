"""Delete fuel stats for re-calculation

Revision ID: d392e4a5a499
Revises: c2cd7a585bbd
Create Date: 2024-05-23 09:39:44.787270

"""
from alembic import op
from datetime import datetime
from sqlalchemy.orm.session import Session
from wps_shared.db.models.auto_spatial_advisory import AdvisoryFuelStats, RunParameters

# revision identifiers, used by Alembic.
revision = 'd392e4a5a499'
down_revision = 'c2cd7a585bbd'
branch_labels = None
depends_on = None


def upgrade():
    session = Session(bind=op.get_bind())
    start_date = datetime(2024, 5, 1)

    # Query for run_parameters IDs based on the start_date
    rp_result = session.query(RunParameters.id).filter(RunParameters.for_date >= start_date).all()
    rp_ids = [row.id for row in rp_result]

    # Delete fuel stats with run_parameters IDs in rp_ids
    session.query(AdvisoryFuelStats).filter(AdvisoryFuelStats.run_parameters.in_(rp_ids)).delete()


def downgrade():
    # No downgrade possible
    pass
