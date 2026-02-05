"""SFMS run tables

Revision ID: 0b46effaf3a1
Revises: cf8397b26783
Create Date: 2026-02-05 13:09:29.529096

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from wps_shared.db.models.common import TZTimeStamp

# revision identifiers, used by Alembic.
revision = '0b46effaf3a1'
down_revision = 'cf8397b26783'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('sfms_run',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('run_type', postgresql.ENUM('forecast', 'actual', name='runtypeenum', create_type=False), nullable=False),
    sa.Column('target_date', sa.Date(), nullable=False),
    sa.Column('run_datetime', TZTimeStamp(), nullable=False),
    sa.Column('stations', sa.ARRAY(sa.Integer()), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    comment='Tracks SFMS job runs and the stations used.'
    )
    op.create_index(op.f('ix_sfms_run_id'), 'sfms_run', ['id'], unique=False)
    op.create_index(op.f('ix_sfms_run_run_datetime'), 'sfms_run', ['run_datetime'], unique=False)
    op.create_index(op.f('ix_sfms_run_run_type'), 'sfms_run', ['run_type'], unique=False)
    op.create_index(op.f('ix_sfms_run_target_date'), 'sfms_run', ['target_date'], unique=False)
    op.create_table(
        "sfms_run_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_name", sa.String(), nullable=False),
        sa.Column("completed_at", TZTimeStamp(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("sfms_run_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["sfms_run_id"],
            ["sfms_run.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Tracks SFMS interpolation runs with execution timestamps and status.",
    )
    op.create_index(op.f('ix_sfms_run_log_id'), 'sfms_run_log', ['id'], unique=False)
    op.create_index(op.f('ix_sfms_run_log_job_name'), 'sfms_run_log', ['job_name'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_sfms_run_log_job_name'), table_name='sfms_run_log')
    op.drop_index(op.f('ix_sfms_run_log_id'), table_name='sfms_run_log')
    op.drop_table('sfms_run_log')
    op.drop_index(op.f('ix_sfms_run_target_date'), table_name='sfms_run')
    op.drop_index(op.f('ix_sfms_run_run_type'), table_name='sfms_run')
    op.drop_index(op.f('ix_sfms_run_run_datetime'), table_name='sfms_run')
    op.drop_index(op.f('ix_sfms_run_id'), table_name='sfms_run')
    op.drop_table('sfms_run')

