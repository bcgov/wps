"""Make observation fields nullable

Revision ID: 05d1dd3062b4
Revises: 1caf3488a340
Create Date: 2021-06-28 12:21:35.022195

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '05d1dd3062b4'
down_revision = '1caf3488a340'
branch_labels = None
depends_on = None


def upgrade():
    """ Make fields in observations table nullable, so that obs with some missing data
    can still be entered into table """
    op.alter_column('hourly_actuals', 'temperature', nullable=True)
    op.alter_column('hourly_actuals', 'relative_humidity', nullable=True)
    op.alter_column('hourly_actuals', 'wind_direction', nullable=True)
    op.alter_column('hourly_actuals', 'wind_speed', nullable=True)
    op.alter_column('hourly_actuals', 'precipitation', nullable=True)
    op.alter_column('hourly_actuals', 'ffmc', nullable=True)
    op.alter_column('hourly_actuals', 'isi', nullable=True)
    op.alter_column('hourly_actuals', 'fwi', nullable=True)


def downgrade():
    """ Do the opposite - return the fields to not-nullable """
    op.alter_column('hourly_actuals', 'temperature', nullable=False)
    op.alter_column('hourly_actuals', 'relative_humidity', nullable=False)
    op.alter_column('hourly_actuals', 'wind_direction', nullable=False)
    op.alter_column('hourly_actuals', 'wind_speed', nullable=False)
    op.alter_column('hourly_actuals', 'precipitation', nullable=False)
    op.alter_column('hourly_actuals', 'ffmc', nullable=False)
    op.alter_column('hourly_actuals', 'isi', nullable=False)
    op.alter_column('hourly_actuals', 'fwi', nullable=False)
