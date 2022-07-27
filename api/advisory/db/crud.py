from sqlalchemy.orm import Session
from advisory.db.models.tileserver import (Hfi, FireZone)
from advisory.db.database.tileserver import get_tileserver_session_scope


def get_hfi_area_percentages(session: Session):
    """ This is terribly slow!

    For each fire zone, it gives you the area of the fire zone, and the area of hfi polygons
    within that fire zone. Using those two values, you can then calculate the percentage of the 
    zone that has a high hfi.
    """
    return session.query(
        FireZone.id,
        FireZone.mof_fire_zone_id,
        FireZone.mof_fire_zone_name,
        FireZone.geom.ST_Transform(3005).ST_Area().label('zone_area'),
        Hfi.wkb_geometry.ST_Union().ST_Intersection(FireZone.geom).ST_Transform(3005).ST_Area().label('hfi_area')
    ).join(Hfi, Hfi.wkb_geometry.ST_Intersects(FireZone.geom)).group_by(FireZone.id)
