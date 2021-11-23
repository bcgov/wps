""" CRUD operations relating to HFI Calculator
"""
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.orm import Session
from app.db.models.thessian_polygon_areas import ThessianPolygonArea


def get_all_fire_zone_areas(session: Session) -> CursorResult:
    """ Get all fire zone areas """
    return session.query(ThessianPolygonArea.geom).all()
