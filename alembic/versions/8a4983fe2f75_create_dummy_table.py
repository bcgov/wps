# pylint: disable=invalid-name, missing-function-docstring
"""create_dummy_table

Revision ID: 8a4983fe2f75
Revises: Creates a dummy table (as an example) to populate empty DB
Create Date: 2020-06-29 10:42:09.543180

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '8a4983fe2f75'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'dummy',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('description', sa.Unicode(200)),
    )
    op.create_table_comment(
        'dummy',
        'An empty dummy table to initialize the DB. Proof-of-concept for manual Alembic migrations.'
    )


def downgrade():
    op.drop_table_comment('dummy')
    op.drop_table('dummy')
