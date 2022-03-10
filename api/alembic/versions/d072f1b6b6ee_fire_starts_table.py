"""Fire starts table

Revision ID: d072f1b6b6ee
Revises: 9a5bb047ae19
Create Date: 2022-03-10 13:05:55.015938

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd072f1b6b6ee'
down_revision = '9a5bb047ae19'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('hfi_fire_starts',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('fire_centre_id', sa.Integer(), nullable=False),
                    sa.Column('min_starts', sa.Integer(), nullable=False),
                    sa.Column('max_starts', sa.Integer(), nullable=False),
                    sa.Column('intensity_group', sa.Integer(), nullable=False),
                    sa.Column('prep_level', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['fire_centre_id'], ['fire_centres.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('fire_centre_id', 'min_starts', 'max_starts',
                                        'intensity_group', name='unique_fire_centre_fire_start_range'),
                    comment='Identifies the unique fire start range and intensity group mapping'
                    )
    op.create_index(op.f('ix_hfi_fire_starts_fire_centre_id'),
                    'hfi_fire_starts', ['fire_centre_id'], unique=False)
    op.create_index(op.f('ix_hfi_fire_starts_intensity_group'),
                    'hfi_fire_starts', ['intensity_group'], unique=False)
    op.create_index(op.f('ix_hfi_fire_starts_max_starts'), 'hfi_fire_starts', ['max_starts'], unique=False)
    op.create_index(op.f('ix_hfi_fire_starts_min_starts'), 'hfi_fire_starts', ['min_starts'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_hfi_fire_starts_min_starts'), table_name='hfi_fire_starts')
    op.drop_index(op.f('ix_hfi_fire_starts_max_starts'), table_name='hfi_fire_starts')
    op.drop_index(op.f('ix_hfi_fire_starts_intensity_group'), table_name='hfi_fire_starts')
    op.drop_index(op.f('ix_hfi_fire_starts_fire_centre_id'), table_name='hfi_fire_starts')
    op.drop_table('hfi_fire_starts')
