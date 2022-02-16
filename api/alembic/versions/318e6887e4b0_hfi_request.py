"""HFI request

Revision ID: 318e6887e4b0
Revises: 839f18e0ecc4
Create Date: 2022-02-11 09:47:20.696293

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '318e6887e4b0'
down_revision = '839f18e0ecc4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('hfi_request',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('fire_centre_id', sa.Integer(), nullable=False),
                    sa.Column('prep_start_day', sa.Date(), nullable=False),
                    sa.Column('prep_end_day', sa.Date(), nullable=False),
                    sa.Column('create_timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
                    sa.Column('create_user', sa.String(), nullable=False),
                    sa.Column('request', sa.JSON(), nullable=True),
                    sa.ForeignKeyConstraint(['fire_centre_id'], ['fire_centres.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('fire_centre_id', 'prep_start_day', 'prep_end_day',
                                        'create_timestamp', name='unique_request_create_timestamp_for_fire_centre'),
                    comment='Identifies the unique code used to identify the station'
                    )
    op.create_index(op.f('ix_hfi_request_create_timestamp'),
                    'hfi_request', ['create_timestamp'], unique=False)
    op.create_index(op.f('ix_hfi_request_fire_centre_id'), 'hfi_request', ['fire_centre_id'], unique=False)
    op.create_index(op.f('ix_hfi_request_prep_end_day'), 'hfi_request', ['prep_end_day'], unique=False)
    op.create_index(op.f('ix_hfi_request_prep_start_day'), 'hfi_request', ['prep_start_day'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_hfi_request_prep_start_day'), table_name='hfi_request')
    op.drop_index(op.f('ix_hfi_request_prep_end_day'), table_name='hfi_request')
    op.drop_index(op.f('ix_hfi_request_fire_centre_id'), table_name='hfi_request')
    op.drop_index(op.f('ix_hfi_request_create_timestamp'), table_name='hfi_request')
    op.drop_table('hfi_request')
