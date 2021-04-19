from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session


def _get_noon_date(date_of_interest: datetime):
    """
    If before noon today, give noon from day before.
    If after noon today, give noon from date of interest.
    """
    noon_for_date_of_interest = datetime(year=date_of_interest.year,
                                         month=date_of_interest.month,
                                         day=date_of_interest.day,
                                         hour=20, tzinfo=timezone.utc)
    if date_of_interest < noon_for_date_of_interest:
        # oh - you want noon for the prevous day
        day_before = date_of_interest - timedelta(days=1)
        return datetime(
            year=day_before.year, month=day_before.month, day=day_before.day, hour=20, tzinfo=timezone.utc)
    # you want noon for today
    return noon_for_date_of_interest


def get_noon_forecast_observation_union(session: Session, date_of_interest: datetime):
    """ Return union of forecasts and observations.
    """
    noon_date = _get_noon_date(date_of_interest)
    query = """
---
--- most recent forecasts
---
select 'forecasts' as record_type, noon_forecasts.weather_date, noon_forecasts.station_code, 
noon_forecasts.temperature, noon_forecasts.relative_humidity
from noon_forecasts
inner join
-- join on max dates
(select 
noon_forecasts.station_code,
max(noon_forecasts.created_at) max_created_at
from noon_forecasts 
where 
	noon_forecasts.weather_date = :weather_date and
	noon_forecasts.temp_valid = True and noon_forecasts.rh_valid = True
group by noon_forecasts.station_code) station_max_dates
on noon_forecasts.station_code = station_max_dates.station_code and 
	noon_forecasts.created_at = station_max_dates.max_created_at

where 
noon_forecasts.weather_date = :weather_date and
	noon_forecasts.temp_valid = True and noon_forecasts.rh_valid = True
-- order by noon_forecasts.station_code
union
---
--- hourly actuals
---
select 'observations' as record_type, hourly_actuals.weather_date, hourly_actuals.station_code,
hourly_actuals.temperature, hourly_actuals.relative_humidity 
from hourly_actuals
where hourly_actuals.weather_date = :weather_date
-- order by hourly_actuals.station_code"""
    return session.execute(query, {"weather_date": noon_date})
