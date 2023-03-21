""" CRUD operations relating to Morecast v2
"""
from typing import List
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from datetime import date, datetime, time
from app.db.models.morecast_v2 import MorecastForecastRecord


def save_all_forecasts(session: Session, forecasts: List[MorecastForecastRecord]):
    session.bulk_save_objects(forecasts)
    session.commit()


def get_user_forecasts_for_date(session: Session, username: str, for_date: date) -> List[MorecastForecastRecord]:
    start_time = datetime.combine(for_date, time.min)
    end_time = datetime.combine(for_date, time.max)

    query = session.query(MorecastForecastRecord)\
        .filter(MorecastForecastRecord.create_user == username)\
        .filter(MorecastForecastRecord.for_date.between(start_time, end_time))
    return query.order_by(MorecastForecastRecord.create_timestamp.desc())


def get_forecasts_in_range(session: Session, start_date: date, end_date: date, stations: List[int]):
    subquery = session.query(
        MorecastForecastRecord.station_code,
        func.max(MorecastForecastRecord.create_timestamp).label("most_recent"),
        MorecastForecastRecord.for_date)\
        .filter(MorecastForecastRecord.for_date.between(start_date, end_date))\
        .filter(MorecastForecastRecord.station_code.in_(stations))\
        .group_by(MorecastForecastRecord.station_code, MorecastForecastRecord.for_date)\
        .subquery()

    query = session.query(MorecastForecastRecord)\
        .join(subquery, and_(
            MorecastForecastRecord.station_code == subquery.c.station_code,
            MorecastForecastRecord.create_timestamp == subquery.c.most_recent,
            MorecastForecastRecord.for_date == subquery.c.for_date
        ))
    return query.all()
