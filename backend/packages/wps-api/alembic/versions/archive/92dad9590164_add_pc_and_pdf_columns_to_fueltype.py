"""Add pc and pdf columns to FuelType
Remove unique constraint from abbrev col in FuelType - will be inserting
fuel types with same abbrev, just different values for PC/PDF.

Revision ID: 92dad9590164
Revises: 4e9664f4962e
Create Date: 2022-02-16 15:20:00.796051

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92dad9590164'
down_revision = '4e9664f4962e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('fuel_types', sa.Column('percentage_conifer', sa.Integer(), nullable=True))
    op.add_column('fuel_types', sa.Column('percentage_dead_fir', sa.Integer(), nullable=True))
    op.add_column('fuel_types', sa.Column('fuel_type_code', sa.String(), nullable=True))
    op.drop_index('ix_fuel_types_abbrev', table_name='fuel_types')
    op.create_index(op.f('ix_fuel_types_abbrev'), 'fuel_types', ['abbrev'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_fuel_types_abbrev'), table_name='fuel_types')
    op.create_index('ix_fuel_types_abbrev', 'fuel_types', ['abbrev'], unique=False)
    op.drop_column('fuel_types', 'percentage_dead_fir')
    op.drop_column('fuel_types', 'percentage_conifer')
    op.drop_column('fuel_types', 'fuel_type_code')
