"""threshold id data import for min win speed

Revision ID: 151ec4aa0b32
Revises: 395caeeeaf77
Create Date: 2025-03-18 14:14:56.569116

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
from wps_shared.db.models.auto_spatial_advisory import (
    HfiClassificationThresholdEnum,
)

# revision identifiers, used by Alembic.
revision = '151ec4aa0b32'
down_revision = '395caeeeaf77'
branch_labels = None
depends_on = None


hfi_classification_threshold_table = sa.Table('advisory_hfi_classification_threshold', sa.MetaData(),
                                sa.Column('id', sa.Integer),
                                sa.Column('description', sa.String),
                                sa.Column('name', sa.String))

advisory_hfi_wind_speed_table = sa.Table('advisory_hfi_wind_speed', sa.MetaData(),
                                sa.Column('id', sa.Integer),
                                sa.Column('threshold', sa.String),
                                sa.Column('threshold_temp', sa.Integer),
                                sa.Column('run_parameters', sa.Integer),
                                sa.Column('min_wind_speed', sa.Float))

def get_hfi_threshold_id(session: Session, threshold_name: HfiClassificationThresholdEnum):
    res = session.query(hfi_classification_threshold_table) \
        .filter(hfi_classification_threshold_table.c.name.ilike(f'{threshold_name.value}%%'))
    return int(res.first().id)


def upgrade():
    session = Session(bind=op.get_bind())
    advisory_threshold_id = get_hfi_threshold_id(session, HfiClassificationThresholdEnum.ADVISORY)
    warning_threshold_id = get_hfi_threshold_id(session, HfiClassificationThresholdEnum.WARNING)

    update_advisory_stmt = advisory_hfi_wind_speed_table\
        .update()\
        .values(threshold_temp=advisory_threshold_id)\
        .where(advisory_hfi_wind_speed_table.c.threshold == HfiClassificationThresholdEnum.ADVISORY.value)
    

    update_warning_stmt = advisory_hfi_wind_speed_table\
        .update()\
        .values(threshold_temp=warning_threshold_id)\
        .where(advisory_hfi_wind_speed_table.c.threshold == HfiClassificationThresholdEnum.WARNING.value)

    session.execute(update_advisory_stmt)
    session.execute(update_warning_stmt)


def downgrade():
    session = Session(bind=op.get_bind())
    downgrade_stmt = advisory_hfi_wind_speed_table.update().values(threshold_temp=None)
    session.execute(downgrade_stmt)
