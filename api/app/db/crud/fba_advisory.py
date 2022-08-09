from datetime import date
from app.db.models.advisory import FireZoneAdvisory
from sqlalchemy.orm import Session


def save_advisory(session: Session, advisory: FireZoneAdvisory):
    session.add(advisory)


def get_advisories(session: Session, today: date):
    return session.query(FireZoneAdvisory).filter(FireZoneAdvisory.for_date == today).all()
