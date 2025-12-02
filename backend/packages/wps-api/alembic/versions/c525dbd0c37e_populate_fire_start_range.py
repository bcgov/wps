"""populate fire start range

Revision ID: c525dbd0c37e
Revises: fe33ab8c6c01
Create Date: 2022-03-15 17:54:47.364533

"""
from alembic import op
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, text


# revision identifiers, used by Alembic.
revision = 'c525dbd0c37e'
down_revision = 'fe33ab8c6c01'
branch_labels = None
depends_on = None


def populate_hfi_fire_start_lookup(op, id, hfi_fire_start_lookup, fire_start_ranges, lookups):
    """ Populate hfi_fire_start_lookup table with lookups for fire start ranges. """
    data = []
    for index, fire_start_range in enumerate(fire_start_ranges):
        for lookup in lookups[index]:
            data.append({'id': id,
                        'fire_start_range_id': fire_start_range['id'],
                         'mean_intensity_group': lookup[0],
                         'prep_level': lookup[1]})
            id += 1
    op.bulk_insert(hfi_fire_start_lookup, data)
    return id


def upgrade():
    """ Populate fire start range data for fire centres.
    """

    # The hfi_request structure has changed, so we need to remove existing records!
    op.execute('DELETE FROM hfi_request')

    # Create an ad-hoc table to use for the insert statement.
    hfi_fire_start_range = table('hfi_fire_start_range',
                                 column('id', Integer),
                                 column('label', String)
                                 )

    # Fire start ranges for kamloops fire centre.
    kamloops_fire_start_ranges = [
        {'id': 1, 'label': '0-1'},
        {'id': 2, 'label': '1-2'},
        {'id': 3, 'label': '2-3'},
        {'id': 4, 'label': '3-6'},
        {'id': 5, 'label': '6+'}
    ]
    op.bulk_insert(hfi_fire_start_range,
                   kamloops_fire_start_ranges
                   )
    # Fire start ranges for the other fire centres.
    other_fire_start_ranges = [
        {'id': 6, 'label': '0-2'},
        {'id': 7, 'label': '3-5'},
        {'id': 8, 'label': '6-10'},
        {'id': 9, 'label': '11-14'},
        {'id': 10, 'label': '15+'}
    ]
    op.bulk_insert(hfi_fire_start_range,
                   other_fire_start_ranges
                   )

    # Create an ad-hoc table to use for the insert statement.
    hfi_fire_centre_fire_start_range = table('hfi_fire_centre_fire_start_range',
                                             column('id', Integer),
                                             column('fire_start_range_id', Integer),
                                             column('fire_centre_id', Integer),
                                             column('order', Integer))

    # Link fire start ranges to each fire centre.
    fire_centre_ranges = []
    conn = op.get_bind()
    res = conn.execute(text('SELECT id, name FROM fire_centres'))
    results = res.fetchall()

    id_count = 1
    for result in results:
        fire_centre_id = result[0]
        name = result[1]
        order_count = 0
        if name == 'Kamloops Fire Centre':
            hfi_fire_start_ranges = kamloops_fire_start_ranges
        else:
            hfi_fire_start_ranges = other_fire_start_ranges
        for fire_start_range in hfi_fire_start_ranges:
            fire_centre_ranges.append(
                {'id': id_count,
                 'fire_start_range_id': fire_start_range['id'],
                 'fire_centre_id': fire_centre_id,
                 'order': order_count})
            order_count += 1
            id_count += 1
    op.bulk_insert(hfi_fire_centre_fire_start_range, fire_centre_ranges)

    # Create an ad-hoc table to use for the insert statement.
    hfi_fire_start_lookup = table('hfi_fire_start_lookup',
                                  column('id', Integer),
                                  column('fire_start_range_id', Integer),
                                  column('mean_intensity_group', Integer),
                                  column('prep_level', Integer)
                                  )

    # Populate lookup values for each fire start range.
    start_id = populate_hfi_fire_start_lookup(op, 1, hfi_fire_start_lookup, kamloops_fire_start_ranges, [
        # 0-1
        [[1, 1], [2, 1], [3, 2], [4, 3], [5, 4]],
        # 1-2
        [[1, 1], [2, 1], [3, 2], [4, 4], [5, 5]],
        # 2-3
        [[1, 2], [2, 3], [3, 4], [4, 5], [5, 6]],
        # 3-6
        [[1, 3], [2, 4], [3, 4], [4, 5], [5, 6]],
        # 6+
        [[1, 4], [2, 5], [3, 6], [4, 6], [5, 6]],
    ])

    populate_hfi_fire_start_lookup(op, start_id, hfi_fire_start_lookup, other_fire_start_ranges, [
        # 0-2
        [[1, 1], [2, 1], [3, 2], [4, 3], [5, 4]],
        # 3-5
        [[1, 1], [2, 2], [3, 3], [4, 4], [5, 5]],
        # 6-10
        [[1, 2], [2, 3], [3, 4], [4, 5], [5, 6]],
        # 11-14
        [[1, 3], [2, 4], [3, 5], [4, 6], [5, 6]],
        # 15+
        [[1, 4], [2, 5], [3, 6], [4, 6], [5, 6]],
    ])


def downgrade():
    op.execute("DELETE FROM hfi_fire_centre_fire_start_range")
    op.execute("DELETE FROM hfi_fire_start_lookup")
    op.execute("DELETE FROM hfi_fire_start_range")
