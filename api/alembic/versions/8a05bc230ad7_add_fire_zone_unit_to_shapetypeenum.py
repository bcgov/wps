"""add fire zone unit to shapetypeenum

Revision ID: 8a05bc230ad7
Revises: 2442f07d975c
Create Date: 2023-10-24 11:04:30.622497

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8a05bc230ad7'
down_revision = '2442f07d975c'
branch_labels = None
depends_on = None

shape_type_table = sa.Table('advisory_shape_types', sa.MetaData(),
                            sa.Column('id', sa.Integer),
                            sa.Column('name', sa.String))


def upgrade():
    # Create a new enum type
    shape_type_new = sa.Enum('fire_centre', 'fire_zone', 'fire_zone_unit', name='shapetypeenum_2', create_type=False)
    conn = op.get_bind()

    shape_type_new.create(bind=conn, checkfirst=True)

    # Alter the column to use the new enum type
    op.execute('ALTER TABLE advisory_shape_types ALTER COLUMN name TYPE shapetypeenum_2 USING name::text::shapetypeenum_2')
    op.execute('DROP TYPE shapetypeenum')


def downgrade():
    conn = op.get_bind()
    # Recreate old new enum type
    shape_type_old = sa.Enum('fire_centre', 'fire_zone', name='shapetypeenum', create_type=False)

    shape_type_old.create(bind=conn, checkfirst=True)

    # Alter the column to use the old enum type
    op.execute('ALTER TABLE advisory_shape_types ALTER COLUMN name TYPE shapetypeenum USING name::text::shapetypeenum')
    op.execute('DROP TYPE shapetypeenum_2')
