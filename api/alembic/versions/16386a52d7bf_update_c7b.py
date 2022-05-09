"""Update C7B

Revision ID: 16386a52d7bf
Revises: 82cc8ffa75ce
Create Date: 2022-05-04 13:46:16.589667

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16386a52d7bf'
down_revision = '82cc8ffa75ce'
branch_labels = None
depends_on = None


def upgrade():
    # Change fuel type code to C7B where abbrev is C7B
    op.execute('UPDATE fuel_types SET fuel_type_code = \'C7B\' WHERE abbrev LIKE \'C7B\'')


def downgrade():
    # Change fuel type code back to C7 where abbrev is C7B
    op.execute('UPDATE fuel_types SET fuel_type_code = \'C7\' WHERE abbrev LIKE \'C7B\'')
