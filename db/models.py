""" Class models that reflect resources and map to database tables
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Sequence, ForeignKey
from sqlalchemy.sql import func
from db.database import BASE


class ForecastModel(BASE):
    """ Weather forecasting model blueprint """
    __tablename__ = 'forecast_model'

    id = Column(Integer, Sequence('forecast_model_id_seq'),
                primary_key=True, nullable=False, index=True)
    name = Column(String, unique=True)
    abbrev = Column(String, unique=True)


class SingleForecast(BASE):
    """ Blueprint for a weather forecast for a single weather station over one time interval
    (time interval varies by forecast model)
    """
    __tablename__ = 'single_forecast'

    id = Column(Integer, Sequence('single_forecast_id_seq'),
                primary_key=True, nullable=False, index=True)
    """ The date and time to which the forecast applies """
    forecast_datetime = Column(DateTime, nullable=False)
    forecast_model = Column(Integer, ForeignKey(
        'forecast_model.id'), nullable=False)
    weather_station = Column(Integer, nullable=False)
    """ The date and time at which the model was run / forecast was issued """
    issue_date = Column(DateTime, nullable=False, default=func.now())
    temperature = Column(Float)
    dew_point = Column(Float)
    relative_humidity = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    total_precipitation = Column(Float)
    accumulated_rain = Column(Float)
    accumulated_snow = Column(Float)
    accumulated_freezing_rain = Column(Float)
    accumulated_ice_pellets = Column(Float)
    cloud_cover = Column(Float)
    sea_level_pressure = Column(Float)
    wind_speed_40m = Column(Float)
    wind_direction_40m = Column(Float)
    wind_direction_80m = Column(Float)
    wind_speed_120m = Column(Float)
    wind_direction_120m = Column(Float)
    wind_speed_925mb = Column(Float)
    wind_direction_925mb = Column(Float)
    wind_speed_850mb = Column(Float)
    wind_direction_850mb = Column(Float)
