"""postgis_extensions_upgrade

Revision ID: ab2064a2f41e
Revises: fbca68ccc9da
Create Date: 2022-09-12 14:16:30.382152

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab2064a2f41e'
down_revision = 'fbca68ccc9da'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('SELECT postgis_extensions_upgrade()')


def downgrade():
    # there's no going back!
    pass
