"""add status to prescription_status

Revision ID: 128156e36f67
Revises: 65d5edb3f200
Create Date: 2025-05-08 15:14:49.193067

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session


# revision identifiers, used by Alembic.
revision = '128156e36f67'
down_revision = '65d5edb3f200'
branch_labels = None
depends_on = None

prescription_status_table = sa.Table(
    'prescription_status',
    sa.MetaData(),
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True)
)

def upgrade():
    session = Session(bind=op.get_bind())
    records = [{
        'description': 'all variables are within range',
        'name': 'all'
    },
        {
        'description': 'hfi is within range',
        'name': 'hfi'
    },
        {
        'description': 'not in prescription',
        'name': 'no'
    }]

    for record in records:
        stmt = prescription_status_table.insert().values(record)
        session.execute(stmt)


def downgrade():
    session = Session(bind=op.get_bind())
    stmt = prescription_status_table.delete()
    session.execute(stmt)
