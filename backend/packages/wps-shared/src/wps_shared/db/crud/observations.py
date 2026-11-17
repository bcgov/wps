"""CRUD operations relating to observed readings (a.k.a "hourlies")"""

import datetime
from typing import List

from sqlalchemy import select, text
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from wps_shared.db.models.observations import HourlyActual


def get_hourly_actuals(
    session: Session, station_codes: List[int], start_date: datetime, end_date: datetime = None
):
    """Query for hourly actuals for given stations, from stated start_date to end_date.

    :param end_date: If specified, return up to and including the end_date
    """
    query = (
        session.query(HourlyActual)
        .filter(HourlyActual.station_code.in_(station_codes))
        .filter(HourlyActual.weather_date >= start_date)
        .filter(HourlyActual.temp_valid == True)
        .filter(HourlyActual.rh_valid == True)
    )
    if end_date is not None:
        query = query.filter(HourlyActual.weather_date <= end_date)
    query = query.order_by(HourlyActual.station_code).order_by(HourlyActual.weather_date)
    return query


def save_hourly_actual(session: Session, hourly_actual: HourlyActual):
    """Abstraction for writing HourlyActual to database."""
    session.add(hourly_actual)
    session.commit()


def get_accumulated_precipitation(
    session: Session, station_code: int, start_datetime: datetime, end_datetime: datetime
):
    """Get the accumulated precipitation for a station by datetime range."""
    stmt = select(func.sum(HourlyActual.precipitation)).where(
        HourlyActual.station_code == station_code,
        HourlyActual.weather_date > start_datetime,
        HourlyActual.weather_date <= end_datetime,
    )
    result = session.scalars(stmt).first()
    if result is None:
        return 0
    return result


def get_accumulated_precip_by_24h_interval(
    session: Session, station_code: int, start_datetime: datetime, end_datetime: datetime
):
    """Get the accumulated precip for 24 hour intervals for a given station code within the specified time interval.
    :param session: The ORM/database session.
    :param station_code: The numeric code identifying the weather station of interest.
    :param start_datetime: The earliest date and time of interest.
    :param end_datetime: The latest date and time of interest.

    Note: I couldn't construct this query in SQLAlchemy, hence the need for the 'text' based query.

    generate_series(\'{}\', \'{}\', '24 hours'::interval)

    This gives us a one column table of dates separated by 24 hours between the start and end dates. For example, if start and end dates are 2023-10-31 20:00:00 to 2023-11-03 20:00:00 we would have a table like:

    day
    2023-10-31 20:00:00
    2023-11-01 20:00:00
    2023-11-02 20:00:00
    2023-11-03 20:00:00

    We then join the HourlyActuals table so that we can sum hourly precip in a 24 hour period. The join is based on the weather_date field in the HourlyActuals table being in a 24 hour range using this odd looking syntax:

    weather_date <@ tstzrange(day, day + '24 hours', '(]')

    Using 2023-10-31 20:00:00 as an example, rows with the following dates would match. The (] syntax means the lower bound is excluded but the upper bound is included.

    2023-10-31 21:00:00
    2023-10-31 22:00:00
    2023-10-31 23:00:00
    2023-11-01 00:00:00
    2023-11-01 01:00:00
    ....
    2023-11-01 19:00:00
    2023-11-01 20:00:00
    """
    stmt = """
        SELECT day, station_code, sum(precipitation) actual_precip_24h
        FROM
            generate_series(\'{}\', \'{}\', '24 hours'::interval) day
        LEFT JOIN
            hourly_actuals
        ON 
            weather_date <@ tstzrange(day - INTERVAL '24 hours', day, '(]')
        WHERE
            station_code = {}
        GROUP BY
            day, station_code;
    """.format(start_datetime, end_datetime, station_code)
    result = session.execute(text(stmt))
    return result.all()
