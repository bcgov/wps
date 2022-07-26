from app.db.database import get_hfi_read_session_scope
from app.db.external_models.fba_advisory import FireZone, Hfi, FireZoneAdvisory
from sqlalchemy.orm import Session


def get_hfi_area_percentages(session: Session):
    """ This is terribly slow!

    For each fire zone, it gives you the area of the fire zone, and the area of hfi polygons
    within that fire zone. Using those two values, you can then calculate the percentage of the 
    zone that has a high hfi.
    """
    with get_hfi_read_session_scope() as session:
        return session.query(
            FireZone.id,
            FireZone.mof_fire_zone_name,
            FireZone.geom.ST_Transform(3005).ST_Area().label('zone_area'),
            Hfi.wkb_geometry.ST_Union().ST_Intersection(FireZone.geom).ST_Transform(3005).ST_Area().label('hfi_area')
        ).join(Hfi, Hfi.wkb_geometry.ST_Intersects(FireZone.geom)).group_by(FireZone.id)
        # for row in q:
        #     zone_area = row.zone_area
        #     hfi_area = row.hfi_area


def save_advisory(session: Session, advisory: FireZoneAdvisory):
    session.add(advisory)


def get_advisories(session: Session):
    return session.query(FireZoneAdvisory).all()
