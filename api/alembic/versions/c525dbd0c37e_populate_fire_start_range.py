"""populate fire start range

Revision ID: c525dbd0c37e
Revises: fe33ab8c6c01
Create Date: 2022-03-15 17:54:47.364533

"""
from alembic import op
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer


# revision identifiers, used by Alembic.
revision = 'c525dbd0c37e'
down_revision = 'fe33ab8c6c01'
branch_labels = None
depends_on = None


def populate_lookups(op, id, hfi_fire_start_lookup, fire_start_ranges, lookups):
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

    # Create an ad-hoc table to use for the insert statement.
    hfi_fire_start_range = table('hfi_fire_start_range',
                                 column('id', Integer),
                                 column('label', String)
                                 )

    # Data for kamloops fire centre.
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
    # Data for the other fire centres.
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
    fire_centre_ranges = []
    conn = op.get_bind()
    res = conn.execute('SELECT id, name FROM fire_centres')
    results = res.fetchall()

    id_count = 1
    for result in results:
        id = result[0]
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
                 'fire_centre_id': id,
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

    id = populate_lookups(op, 1, hfi_fire_start_lookup, kamloops_fire_start_ranges, [
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

    populate_lookups(op, id, hfi_fire_start_lookup, other_fire_start_ranges, [
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

    # op.bulk_insert(hfi_fire_start_lookup, [
    #     # 0-1
    #     {'id': 1, 'fire_start_range_id': hfi_fire_start_ranges[0]
    #         ['id'], 'mean_intensity_group': 1, 'prep_level': 1},
    #     {'id': 2, 'fire_start_range_id': hfi_fire_start_ranges[0]
    #         ['id'], 'mean_intensity_group': 2, 'prep_level': 1},
    #     {'id': 3, 'fire_start_range_id': hfi_fire_start_ranges[0]
    #         ['id'], 'mean_intensity_group': 3, 'prep_level': 2},
    #     {'id': 4, 'fire_start_range_id': hfi_fire_start_ranges[0]
    #         ['id'], 'mean_intensity_group': 4, 'prep_level': 3},
    #     {'id': 5, 'fire_start_range_id': hfi_fire_start_ranges[0]
    #         ['id'], 'mean_intensity_group': 5, 'prep_level': 4},
    #     # 1-2
    #     {'id': 6, 'fire_start_range_id': hfi_fire_start_ranges[1]
    #         ['id'], 'mean_intensity_group': 1, 'prep_level': 1},
    #     {'id': 7, 'fire_start_range_id': hfi_fire_start_ranges[1]
    #         ['id'], 'mean_intensity_group': 2, 'prep_level': 1},
    #     {'id': 8, 'fire_start_range_id': hfi_fire_start_ranges[1]
    #         ['id'], 'mean_intensity_group': 3, 'prep_level': 2},
    #     {'id': 9, 'fire_start_range_id': hfi_fire_start_ranges[1]
    #         ['id'], 'mean_intensity_group': 4, 'prep_level': 4},
    #     {'id': 10, 'fire_start_range_id': hfi_fire_start_ranges[1]
    #         ['id'], 'mean_intensity_group': 5, 'prep_level': 5},
    #     # 2-3
    #     {'id': 11, 'fire_start_range_id': hfi_fire_start_ranges[2]
    #         ['id'], 'mean_intensity_group': 1, 'prep_level': 2},
    #     {'id': 12, 'fire_start_range_id': hfi_fire_start_ranges[2]
    #         ['id'], 'mean_intensity_group': 2, 'prep_level': 3},
    #     {'id': 13, 'fire_start_range_id': hfi_fire_start_ranges[2]
    #         ['id'], 'mean_intensity_group': 3, 'prep_level': 4},
    #     {'id': 14, 'fire_start_range_id': hfi_fire_start_ranges[2]
    #         ['id'], 'mean_intensity_group': 4, 'prep_level': 5},
    #     {'id': 15, 'fire_start_range_id': hfi_fire_start_ranges[2]
    #         ['id'], 'mean_intensity_group': 5, 'prep_level': 6},
    #     # 3-6
    #     {'id': 16, 'fire_start_range_id': hfi_fire_start_ranges[3]
    #         ['id'], 'mean_intensity_group': 1, 'prep_level': 3},
    #     {'id': 17, 'fire_start_range_id': hfi_fire_start_ranges[3]
    #         ['id'], 'mean_intensity_group': 2, 'prep_level': 4},
    #     {'id': 18, 'fire_start_range_id': hfi_fire_start_ranges[3]
    #         ['id'], 'mean_intensity_group': 3, 'prep_level': 4},
    #     {'id': 19, 'fire_start_range_id': hfi_fire_start_ranges[3]
    #         ['id'], 'mean_intensity_group': 4, 'prep_level': 5},
    #     {'id': 20, 'fire_start_range_id': hfi_fire_start_ranges[3]
    #         ['id'], 'mean_intensity_group': 5, 'prep_level': 6},
    #     # 6+
    #     {'id': 21, 'fire_start_range_id': hfi_fire_start_ranges[4]
    #         ['id'], 'mean_intensity_group': 1, 'prep_level': 4},
    #     {'id': 22, 'fire_start_range_id': hfi_fire_start_ranges[4]
    #         ['id'], 'mean_intensity_group': 2, 'prep_level': 5},
    #     {'id': 23, 'fire_start_range_id': hfi_fire_start_ranges[4]
    #         ['id'], 'mean_intensity_group': 3, 'prep_level': 6},
    #     {'id': 24, 'fire_start_range_id': hfi_fire_start_ranges[4]
    #         ['id'], 'mean_intensity_group': 4, 'prep_level': 6},
    #     {'id': 25, 'fire_start_range_id': hfi_fire_start_ranges[4]
    #         ['id'], 'mean_intensity_group': 5, 'prep_level': 6},
    # ])


def downgrade():
    op.execute("DELETE FROM hfi_fire_centre_fire_start_range")
    op.execute("DELETE FROM hfi_fire_start_lookup")
    op.execute("DELETE FROM hfi_fire_start_range")
