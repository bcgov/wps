""" CRUD operations relating to HFI Calculator
"""
from typing import List
from sqlalchemy.orm import Session
from datetime import date, datetime, time
from app.db.models.morecast_v2 import MorecastForecastRecord


def save_all_forecasts(session: Session, forecasts: MorecastForecastRecord):
    session.bulk_save_objects(forecasts)
    session.commit()


def get_user_forecasts_for_date(session: Session, username: str, for_date: date) -> List[MorecastForecastRecord]:
    start_time = datetime.combine(for_date, time.min)
    end_time = datetime.combine(for_date, time.max)

    query = session.query(MorecastForecastRecord)\
        .filter(MorecastForecastRecord.create_user == username)\
        .filter(MorecastForecastRecord.for_date.between(start_time, end_time))
    return query.order_by(MorecastForecastRecord.create_timestamp.desc())
