"""Fire starts table initial data

Revision ID: 362b687a9703
Revises: d072f1b6b6ee
Create Date: 2022-03-10 13:29:05.603627

"""
from alembic import op
from sqlalchemy.orm import Session

from app.db.models.hfi_calc import FireCentre, HFIFireStarts


# revision identifiers, used by Alembic.
revision = '362b687a9703'
down_revision = 'd072f1b6b6ee'
branch_labels = None
depends_on = None
max_int = 2147483647


def upgrade():
    bind = op.get_bind()
    s = Session(bind=bind)
    for (fire_centre) in s.query(FireCentre):
        if fire_centre.id == 1:
            seed_kamloops_data(fire_centre, s)
        else:
            seed_standard_data(fire_centre, s)
    s.commit()


def seed_kamloops_data(kamloops_fire_centre: FireCentre, s: Session):
    """ Seed IG to prep level data specific to kamloops (0 - 6+) """
    objects = [
        # 0 to 1
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=0,
                      max_starts=1,
                      intensity_group=1,
                      prep_level=1),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=0,
                      max_starts=1,
                      intensity_group=2,
                      prep_level=1),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=0,
                      max_starts=1,
                      intensity_group=3,
                      prep_level=2),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=0,
                      max_starts=1,
                      intensity_group=4,
                      prep_level=3),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=0,
                      max_starts=1,
                      intensity_group=5,
                      prep_level=4),
        # 1-2
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=1,
                      max_starts=2,
                      intensity_group=1,
                      prep_level=1),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=1,
                      max_starts=2,
                      intensity_group=2,
                      prep_level=2),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=1,
                      max_starts=2,
                      intensity_group=3,
                      prep_level=3),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=1,
                      max_starts=2,
                      intensity_group=4,
                      prep_level=4),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=1,
                      max_starts=2,
                      intensity_group=5,
                      prep_level=5),
        # 2-3
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=2,
                      max_starts=3,
                      intensity_group=1,
                      prep_level=2),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=2,
                      max_starts=3,
                      intensity_group=2,
                      prep_level=3),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=2,
                      max_starts=3,
                      intensity_group=3,
                      prep_level=4),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=2,
                      max_starts=3,
                      intensity_group=4,
                      prep_level=5),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=2,
                      max_starts=3,
                      intensity_group=5,
                      prep_level=6),
        # 3-6
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=3,
                      max_starts=6,
                      intensity_group=1,
                      prep_level=3),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=3,
                      max_starts=6,
                      intensity_group=2,
                      prep_level=4),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=3,
                      max_starts=6,
                      intensity_group=3,
                      prep_level=5),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=3,
                      max_starts=6,
                      intensity_group=4,
                      prep_level=6),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=3,
                      max_starts=6,
                      intensity_group=5,
                      prep_level=6),
        # 6+
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=6,
                      max_starts=max_int,
                      intensity_group=1,
                      prep_level=4),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=6,
                      max_starts=max_int,
                      intensity_group=2,
                      prep_level=5),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=6,
                      max_starts=max_int,
                      intensity_group=3,
                      prep_level=6),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=6,
                      max_starts=max_int,
                      intensity_group=4,
                      prep_level=6),
        HFIFireStarts(fire_centre_id=kamloops_fire_centre.id,
                      min_starts=6,
                      max_starts=max_int,
                      intensity_group=5,
                      prep_level=6)
    ]
    s.bulk_save_objects(objects)


def seed_standard_data(fire_centre: FireCentre, s: Session):
    """ Seed IG to prep level standard data (0 - 15+) """
    objects = [
        # 0 to 2
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=0,
                      max_starts=2,
                      intensity_group=1,
                      prep_level=1),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=0,
                      max_starts=2,
                      intensity_group=2,
                      prep_level=1),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=0,
                      max_starts=2,
                      intensity_group=3,
                      prep_level=2),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=0,
                      max_starts=2,
                      intensity_group=4,
                      prep_level=3),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=0,
                      max_starts=2,
                      intensity_group=5,
                      prep_level=4),
        # 3 to 5
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=3,
                      max_starts=5,
                      intensity_group=1,
                      prep_level=1),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=3,
                      max_starts=5,
                      intensity_group=2,
                      prep_level=2),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=3,
                      max_starts=5,
                      intensity_group=3,
                      prep_level=3),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=3,
                      max_starts=5,
                      intensity_group=4,
                      prep_level=4),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=3,
                      max_starts=5,
                      intensity_group=5,
                      prep_level=5),
        # 6 to 10
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=6,
                      max_starts=10,
                      intensity_group=1,
                      prep_level=2),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=6,
                      max_starts=10,
                      intensity_group=2,
                      prep_level=3),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=6,
                      max_starts=10,
                      intensity_group=3,
                      prep_level=4),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=6,
                      max_starts=10,
                      intensity_group=4,
                      prep_level=5),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=6,
                      max_starts=10,
                      intensity_group=5,
                      prep_level=6),
        # 11 to 14
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=11,
                      max_starts=14,
                      intensity_group=1,
                      prep_level=3),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=11,
                      max_starts=14,
                      intensity_group=2,
                      prep_level=4),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=11,
                      max_starts=14,
                      intensity_group=3,
                      prep_level=5),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=11,
                      max_starts=14,
                      intensity_group=4,
                      prep_level=6),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=11,
                      max_starts=14,
                      intensity_group=5,
                      prep_level=6),
        # 15+
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=15,
                      max_starts=max_int,
                      intensity_group=1,
                      prep_level=4),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=15,
                      max_starts=max_int,
                      intensity_group=2,
                      prep_level=5),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=15,
                      max_starts=max_int,
                      intensity_group=3,
                      prep_level=6),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=15,
                      max_starts=max_int,
                      intensity_group=4,
                      prep_level=6),
        HFIFireStarts(fire_centre_id=fire_centre.id,
                      min_starts=15,
                      max_starts=max_int,
                      intensity_group=5,
                      prep_level=6)
    ]
    s.bulk_save_objects(objects)


def downgrade():
    bind = op.get_bind()
    s = Session(bind=bind)
    s.query(HFIFireStarts).delete()
    s.commit()
