""" Class models that reflect resources and map to database tables
"""
import datetime
from datetime import timezone
import math
from sqlalchemy import (Column, String, Integer, Float, Boolean,
                        TIMESTAMP, Sequence, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from geoalchemy2 import Geometry
from app.db.database import Base
from app import time_utils


class ProcessedModelRunUrl(Base):
    """ Record to indicate that a particular model run file has been processed.
    NOTE: One could check if values for a particular model run exists, but that would make it more
    difficult to re-process files as you'd have to delete existing values.
    """
    __tablename__ = 'processed_model_run_urls'
    __table_args__ = (
        {'comment': 'Record to indicate that a particular model run file has been processed.'})
    # Unique identifier.
    id = Column(Integer, Sequence('processed_model_run_url_id_seq'),
                primary_key=True, nullable=False, index=True)
    # Source URL of file processed.
    url = Column(String, nullable=False, unique=True)
    # Date this record was created.
    create_date = Column(TIMESTAMP(timezone=True), nullable=False)
    # Date this record was updated.
    update_date = Column(TIMESTAMP(timezone=True), nullable=False)


class PredictionModel(Base):
    """ Identifies the Weather Prediction model (e.g. GDPS 15km resolution). """
    __tablename__ = 'prediction_models'
    __table_args__ = (
        UniqueConstraint('abbreviation', 'projection'),
        {'comment': 'Identifies the Weather Prediction model'}
    )

    id = Column(Integer, Sequence('prediction_models_id_seq'),
                primary_key=True, nullable=False, index=True)
    # E.g. Global Deterministic Prediction System
    name = Column(String, nullable=False)
    # E.g. GDPS
    abbreviation = Column(String, nullable=False)
    # E.g. latlon.15x15
    # NOTE: we may want to consider not bothering with projection, since we would store it as geopgraphical
    # regardles. A better approach may be to just store the resolution: "15x15"
    projection = Column(String, nullable=False)

    def __str__(self):
        return ('id:{self.id}, '
                'name:{self.name}, '
                'abbreviation:{self.abbreviation}, '
                'projection:{self.projection}'.format(self=self))


class PredictionModelRunTimestamp(Base):
    """ Identify which prediction model run (e.g.  2020 07 07 12:00)."""
    __tablename__ = 'prediction_model_run_timestamps'
    __table_args__ = (
        UniqueConstraint('prediction_model_id', 'prediction_run_timestamp'),
        {
            'comment':
            'Identify which prediction model run (e.g.  2020 07 07 12:00).'
        }
    )

    id = Column(Integer, Sequence('prediction_model_run_timestamps_id_seq'),
                primary_key=True, nullable=False, index=True)
    # Is it GPDS or RDPS?
    prediction_model_id = Column(Integer, ForeignKey(
        'prediction_models.id'), nullable=False)
    prediction_model = relationship("PredictionModel")
    # The date and time of the model run.
    prediction_run_timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    # Indicate if this particular model run is completely downloaded.
    complete = Column(Boolean, nullable=False)

    def __str__(self):
        return ('id:{self.id}, '
                'prediction_model:{self.prediction_model.abbreviation}:{self.prediction_model.projection}, '
                'prediction_run_timestamp:{self.prediction_run_timestamp}, '
                'complete={self.complete}').format(self=self)


class PredictionModelGridSubset(Base):
    """ Identify the vertices surrounding the area of interest """
    __tablename__ = 'prediction_model_grid_subsets'
    __table_args__ = (
        UniqueConstraint('prediction_model_id', 'geom'),
        {'comment': 'Identify the vertices surrounding the area of interest'}
    )

    id = Column(Integer, Sequence('prediction_model_grid_subsets_id_seq'),
                primary_key=True, nullable=False, index=True)
    # Which model does this grid belong to? e.g. GDPS latlon.15x.15?
    prediction_model_id = Column(Integer, ForeignKey(
        'prediction_models.id'), nullable=False)
    prediction_model = relationship("PredictionModel")
    # Order of vertices is important!
    # 1st vertex top left, 2nd vertex top right, 3rd vertex bottom right, 4th vertex bottom left.
    geom = Column(Geometry('POLYGON'), nullable=False)


class ModelRunGridSubsetPrediction(Base):
    """ The prediction for a particular model grid subset.
    Each value is an array that corresponds to the vertex in the prediction bounding polygon. """
    __tablename__ = 'model_run_grid_subset_predictions'
    __table_args__ = (
        UniqueConstraint('prediction_model_run_timestamp_id', 'prediction_model_grid_subset_id',
                         'prediction_timestamp'),
        {'comment': 'The prediction for a grid subset of a particular model run.'}
    )

    id = Column(Integer, Sequence('model_run_grid_subset_predictions_id_seq'),
                primary_key=True, nullable=False, index=True)
    # Which model run does this forecacst apply to? E.g. The GDPS 15x.15 run from 2020 07 07 12h00.
    prediction_model_run_timestamp_id = Column(Integer, ForeignKey(
        'prediction_model_run_timestamps.id'), nullable=False)
    prediction_model_run_timestamp = relationship(
        "PredictionModelRunTimestamp", foreign_keys=[prediction_model_run_timestamp_id])
    # Which grid does this prediction apply to?
    prediction_model_grid_subset_id = Column(Integer, ForeignKey(
        'prediction_model_grid_subsets.id'), nullable=False)
    prediction_model_grid_subset = relationship("PredictionModelGridSubset")
    # The date and time to which the prediction applies.
    prediction_timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    # Temperature 2m above model layer.
    tmp_tgl_2 = Column(ARRAY(Float), nullable=True)
    # Relative humidity 2m above model layer.
    rh_tgl_2 = Column(ARRAY(Float), nullable=True)


class NoonForecast(Base):
    """ Class representing table structure of 'noon_forecasts' table in DB.
    Default float values of math.nan are used for the weather variables that are
    sometimes null (None), because Postgres evaluates None != None, so the unique
    constraint doesn't work on records with >=1 None values. But math.nan == math.nan
    """
    __tablename__ = 'noon_forecasts'
    __table_args__ = (
        UniqueConstraint('weather_date',
                         'station_code',
                         'temp_valid',
                         'temperature',
                         'rh_valid',
                         'relative_humidity',
                         'wdir_valid',
                         'wind_direction',
                         'wspeed_valid',
                         'wind_speed',
                         'precip_valid',
                         'precipitation',
                         'gc',
                         'ffmc',
                         'dmc',
                         'dc',
                         'isi',
                         'bui',
                         'fwi',
                         'danger_rating'),
        {'comment': 'The noon_forecast for a weather station and weather date.'}
    )
    id = Column(Integer, primary_key=True)
    weather_date = Column(TIMESTAMP(timezone=True), nullable=False)
    station_code = Column(Integer, nullable=False)
    temp_valid = Column(Boolean, default=False, nullable=False)
    temperature = Column(Float, nullable=False)
    rh_valid = Column(Boolean, default=False, nullable=False)
    relative_humidity = Column(Float, nullable=False)
    wdir_valid = Column(Boolean, default=False, nullable=False)
    # Set default wind_direction to NaN because some stations don't report it
    wind_direction = Column(Float, nullable=False, default=math.nan)
    wspeed_valid = Column(Boolean, default=False, nullable=False)
    wind_speed = Column(Float, nullable=False)
    precip_valid = Column(Boolean, default=False, nullable=False)
    precipitation = Column(Float, nullable=False)
    gc = Column(Float, nullable=False, default=math.nan)
    ffmc = Column(Float, nullable=False, default=math.nan)
    dmc = Column(Float, nullable=False, default=math.nan)
    dc = Column(Float, nullable=False, default=math.nan)
    isi = Column(Float, nullable=False, default=math.nan)
    bui = Column(Float, nullable=False, default=math.nan)
    fwi = Column(Float, nullable=False, default=math.nan)
    danger_rating = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        default=time_utils.get_utc_now())

    def __str__(self):
        return (
            'weather_date:{self.weather_date}, '
            'created_at:{self.created_at}, '
            'temp={self.temperature}, '
            'ffmc={self.ffmc}'
        ).format(self=self)
