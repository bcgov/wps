"""classification thresholds

Revision ID: fbca68ccc9da
Revises: 00df3c7b5cba
Create Date: 2022-09-08 13:09:24.894403

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session


# revision identifiers, used by Alembic.
revision = 'fbca68ccc9da'
down_revision = '00df3c7b5cba'
branch_labels = None
depends_on = None

classification_threshold_table = sa.Table(
    'advisory_hfi_classification_threshold',
    sa.MetaData(),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
)


def upgrade():
    session = Session(bind=op.get_bind())
    records = [{
        'description': '4000 < hfi < 10000',
        'name': 'advisory'
    },
        {
        'description': 'hfi >= 10000',
        'name': 'warning'
    }]

    for record in records:
        stmt = classification_threshold_table.insert().values(record)
        session.execute(stmt)


def downgrade():
    session = Session(bind=op.get_bind())
    stmt = classification_threshold_table.delete()
    session.execute(stmt)
