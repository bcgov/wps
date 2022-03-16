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


def upgrade():
    # Create an ad-hoc table to use for the insert statement.
    hfi_fire_start_range = table('hfi_fire_start_range',
                                 column('id', Integer),
                                 column('label', String)
                                 )

    hfi_fire_start_ranges = [
        {'id': 1, 'label': '0-1'},
        {'id': 2, 'label': '1-2'},
        {'id': 3, 'label': '2-3'},
        {'id': 4, 'label': '3-6'},
        {'id': 5, 'label': '6+'}
    ]
    op.bulk_insert(hfi_fire_start_range,
                   hfi_fire_start_ranges
                   )

    hfi_fire_centre_fire_start_range = table('hfi_fire_centre_fire_start_range',
                                             column('id', Integer),
                                             column('fire_start_range_id', Integer),
                                             column('fire_centre_id', Integer),
                                             column('order', Integer))
    fire_centre_ranges = []
    conn = op.get_bind()
    res = conn.execute('SELECT id FROM fire_centres')
    results = res.fetchall()

    id_count = 1
    for result in results:
        order_count = 0
        for fire_start_range in hfi_fire_start_ranges:
            fire_centre_ranges.append(
                {'id': id_count,
                 'fire_start_range_id': fire_start_range['id'],
                 'fire_centre_id': result[0],
                 'order': order_count})
            order_count += 1
            id_count += 1
    op.bulk_insert(hfi_fire_centre_fire_start_range, fire_centre_ranges)

    hfi_fire_start_lookup = table('hfi_fire_start_lookup',
                                  column('id', Integer),
                                  column('fire_start_range_id', Integer),
                                  column('mean_intensity_group', Integer),
                                  column('prep_level', Integer)
                                  )

    op.bulk_insert(hfi_fire_start_lookup, [
        # 0-1
        {'id': 1, 'fire_start_range_id': hfi_fire_start_ranges[0]
            ['id'], 'mean_intensity_group': 1, 'prep_level': 1},
        {'id': 2, 'fire_start_range_id': hfi_fire_start_ranges[0]
            ['id'], 'mean_intensity_group': 2, 'prep_level': 1},
        {'id': 3, 'fire_start_range_id': hfi_fire_start_ranges[0]
            ['id'], 'mean_intensity_group': 3, 'prep_level': 2},
        {'id': 4, 'fire_start_range_id': hfi_fire_start_ranges[0]
            ['id'], 'mean_intensity_group': 4, 'prep_level': 3},
        {'id': 5, 'fire_start_range_id': hfi_fire_start_ranges[0]
            ['id'], 'mean_intensity_group': 5, 'prep_level': 4},
        # 1-2
        {'id': 6, 'fire_start_range_id': hfi_fire_start_ranges[1]
            ['id'], 'mean_intensity_group': 1, 'prep_level': 1},
        {'id': 7, 'fire_start_range_id': hfi_fire_start_ranges[1]
            ['id'], 'mean_intensity_group': 2, 'prep_level': 1},
        {'id': 8, 'fire_start_range_id': hfi_fire_start_ranges[1]
            ['id'], 'mean_intensity_group': 3, 'prep_level': 2},
        {'id': 9, 'fire_start_range_id': hfi_fire_start_ranges[1]
            ['id'], 'mean_intensity_group': 4, 'prep_level': 4},
        {'id': 10, 'fire_start_range_id': hfi_fire_start_ranges[1]
            ['id'], 'mean_intensity_group': 5, 'prep_level': 5},
        # 2-3
        {'id': 11, 'fire_start_range_id': hfi_fire_start_ranges[2]
            ['id'], 'mean_intensity_group': 1, 'prep_level': 2},
        {'id': 12, 'fire_start_range_id': hfi_fire_start_ranges[2]
            ['id'], 'mean_intensity_group': 2, 'prep_level': 3},
        {'id': 13, 'fire_start_range_id': hfi_fire_start_ranges[2]
            ['id'], 'mean_intensity_group': 3, 'prep_level': 4},
        {'id': 14, 'fire_start_range_id': hfi_fire_start_ranges[2]
            ['id'], 'mean_intensity_group': 4, 'prep_level': 5},
        {'id': 15, 'fire_start_range_id': hfi_fire_start_ranges[2]
            ['id'], 'mean_intensity_group': 5, 'prep_level': 6},
        # 3-6
        {'id': 16, 'fire_start_range_id': hfi_fire_start_ranges[3]
            ['id'], 'mean_intensity_group': 1, 'prep_level': 3},
        {'id': 17, 'fire_start_range_id': hfi_fire_start_ranges[3]
            ['id'], 'mean_intensity_group': 2, 'prep_level': 4},
        {'id': 18, 'fire_start_range_id': hfi_fire_start_ranges[3]
            ['id'], 'mean_intensity_group': 3, 'prep_level': 4},
        {'id': 19, 'fire_start_range_id': hfi_fire_start_ranges[3]
            ['id'], 'mean_intensity_group': 4, 'prep_level': 5},
        {'id': 20, 'fire_start_range_id': hfi_fire_start_ranges[3]
            ['id'], 'mean_intensity_group': 5, 'prep_level': 6},
        # 6+
        {'id': 21, 'fire_start_range_id': hfi_fire_start_ranges[4]
            ['id'], 'mean_intensity_group': 1, 'prep_level': 4},
        {'id': 22, 'fire_start_range_id': hfi_fire_start_ranges[4]
            ['id'], 'mean_intensity_group': 2, 'prep_level': 5},
        {'id': 23, 'fire_start_range_id': hfi_fire_start_ranges[4]
            ['id'], 'mean_intensity_group': 3, 'prep_level': 6},
        {'id': 24, 'fire_start_range_id': hfi_fire_start_ranges[4]
            ['id'], 'mean_intensity_group': 4, 'prep_level': 6},
        {'id': 25, 'fire_start_range_id': hfi_fire_start_ranges[4]
            ['id'], 'mean_intensity_group': 5, 'prep_level': 6},
    ])


def downgrade():
    op.execute("DELETE FROM hfi_fire_centre_fire_start_range")
    op.execute("DELETE FROM hfi_fire_start_lookup")
    op.execute("DELETE FROM hfi_fire_start_range")
