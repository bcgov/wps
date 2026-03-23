"""Four panel charts

Revision ID: 591bf3e24705
Revises: e2d8fc626235
Create Date: 2026-03-23 13:25:08.190313

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from wps_shared.db.models.common import TZTimeStamp

# revision identifiers, used by Alembic.
revision = '591bf3e24705'
down_revision = 'e2d8fc626235'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('processed_four_panel_chart',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('model', sa.String(), nullable=False),
    sa.Column('model_run_timestamp', TZTimeStamp(), nullable=False),
    sa.Column('status', sa.Enum('COMPLETE', 'INPROGRESS', 'FAILED', name='chartstatusenum'), nullable=False),
    sa.Column('create_date', TZTimeStamp(), nullable=False),
    sa.Column('update_date', TZTimeStamp(), nullable=False),
    sa.CheckConstraint("model IN ('GDPS', 'RDPS')", name='chk_model_name_four_panel_charts'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_processed_four_panel_chart_id'), 'processed_four_panel_chart', ['id'], unique=False)
    op.create_index(op.f('ix_processed_four_panel_chart_model'), 'processed_four_panel_chart', ['model'], unique=False)
    op.create_index(op.f('ix_processed_four_panel_chart_model_run_timestamp'), 'processed_four_panel_chart', ['model_run_timestamp'], unique=False)
    op.create_index(op.f('ix_processed_four_panel_chart_status'), 'processed_four_panel_chart', ['status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_processed_four_panel_chart_status'), table_name='processed_four_panel_chart')
    op.drop_index(op.f('ix_processed_four_panel_chart_model_run_timestamp'), table_name='processed_four_panel_chart')
    op.drop_index(op.f('ix_processed_four_panel_chart_model'), table_name='processed_four_panel_chart')
    op.drop_index(op.f('ix_processed_four_panel_chart_id'), table_name='processed_four_panel_chart')
    op.drop_table('processed_four_panel_chart')
    op.execute("DROP TYPE chartstatusenum;")