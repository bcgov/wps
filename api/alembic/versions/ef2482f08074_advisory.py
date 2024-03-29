"""Advisory

Revision ID: ef2482f08074
Revises: c04f22e31997
Create Date: 2022-07-26 18:43:07.572588

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef2482f08074'
down_revision = 'c04f22e31997'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('advisory_fire_zones',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('mof_fire_zone_id', sa.Integer(), nullable=False),
                    sa.Column('elevated_hfi_area', sa.Float(), nullable=False),
                    sa.Column('elevated_hfi_percentage', sa.Float(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Information about advisories.'
                    )
    op.create_index(op.f('ix_advisory_fire_zones_id'), 'advisory_fire_zones', ['id'], unique=False)
    op.create_index(op.f('ix_advisory_fire_zones_mof_fire_zone_id'),
                    'advisory_fire_zones', ['mof_fire_zone_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_advisory_fire_zones_mof_fire_zone_id'), table_name='advisory_fire_zones')
    op.drop_index(op.f('ix_advisory_fire_zones_id'), table_name='advisory_fire_zones')
    op.drop_table('advisory_fire_zones')
    # ### end Alembic commands ###
