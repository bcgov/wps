""" Class models that reflect resources and map to database tables relating to weather models.
"""
import logging
from sqlalchemy import (Column, String, Integer, Float, Boolean,
                        Sequence, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from geoalchemy2 import Geometry
from app.db.database import Base
import app.time_utils as time_utils
from app.db.models.common import TZTimeStamp

logger = logging.getLogger(__name__)


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
    create_date = Column(TZTimeStamp, nullable=False)
    # Date this record was updated.
    update_date = Column(TZTimeStamp, nullable=False)


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
    prediction_run_timestamp = Column(TZTimeStamp, nullable=False)
    # Indicate if this particular model run is completely downloaded.
    complete = Column(Boolean, nullable=False)
    # Indicate if this model run has been interpolated for weather stations.
    interpolated = Column(Boolean, nullable=False)

    def __str__(self):
        return ('id:{self.id}, '
                'prediction_model:{self.prediction_model.abbreviation}:{self.prediction_model.projection}, '
                'prediction_run_timestamp:{self.prediction_run_timestamp}, '
                'complete={self.complete}').format(self=self)


class CHainesPoly(Base):
    """ C-Haines polygons """
    __tablename__ = 'prediction_model_c_haines_polygons'

    id = Column(Integer, Sequence('prediction_model_c_haines_polygons_id_seq'),
                primary_key=True, nullable=False, index=True)
    geom = Column(Geometry('POLYGON'), nullable=False)
    # Depending on the severity of the C-Haines index, we generate
    # severity numbers. (Fire Behaviour analysts only care of the
    # C-Haines is high)
    severity = Column(Integer, nullable=False)
    prediction_timestamp = Column(TZTimeStamp, nullable=False)
    model_run_timestamp = Column(TZTimeStamp, nullable=False)
    prediction_model_id = Column(Integer, ForeignKey(
        'prediction_models.id'), nullable=False)
    prediction_model = relationship("PredictionModel")


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

    def __str__(self):
        return ('id: {self.id}, '
                'prediction_model_id: {self.prediction_model_id}'
                ).format(self=self)


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
    prediction_timestamp = Column(TZTimeStamp, nullable=False)
    # Temperature 2m above model layer.
    tmp_tgl_2 = Column(ARRAY(Float), nullable=True)
    # Relative humidity 2m above model layer.
    rh_tgl_2 = Column(ARRAY(Float), nullable=True)
    # Accumulated precipitation (units kg.m^-2)
    apcp_sfc_0 = Column(ARRAY(Float), nullable=True)
    # Wind direction 10m above ground.
    wdir_tgl_10 = Column(ARRAY(Float), nullable=True)
    # Wind speed 10m above ground.
    wind_tgl_10 = Column(ARRAY(Float), nullable=True)

    def __str__(self):
        return ('id:{self.id}, '
                'prediction_model_run_timestamp_id:{self.prediction_model_run_timestamp_id}, '
                'prediction_model_grid_subset_id:{self.prediction_model_grid_subset_id}, '
                'prediction_timestamp={self.prediction_timestamp}, '
                'tmp_tgl_2={self.tmp_tgl_2}, '
                'rh_tgl_2={self.rh_tgl_2}, '
                'apcp_sfc_0={self.apcp_sfc_0}'
                'wdir_tgl_10={self.wdir_tgl_10}'
                'wind_tgl_10={self.wind_tgl_10}').format(self=self)


class WeatherStationModelPrediction(Base):
    """ The model prediction for a particular weather station.
    Based on values from ModelRunGridSubsetPrediction, but captures linear interpolations based on weather
    station's location within the grid_subset, and also captures time-based linear interpolations where
    needed for certain Model types. """
    __tablename__ = 'weather_station_model_predictions'
    __table_args__ = (
        UniqueConstraint(
            'station_code', 'prediction_model_run_timestamp_id', 'prediction_timestamp'),
        {'comment': 'The interpolated weather values for a weather station, weather date, and model run'}
    )

    id = Column(Integer, Sequence('weather_station_model_predictions_id_seq'),
                primary_key=True, nullable=False, index=True)
    # The 3-digit code for the weather station to which the prediction applies
    station_code = Column(Integer, nullable=False)
    # Which PredictionModelRunTimestamp is this station's prediction based on?
    prediction_model_run_timestamp_id = Column(Integer, ForeignKey(
        'prediction_model_run_timestamps.id'), nullable=False)
    prediction_model_run_timestamp = relationship(
        "PredictionModelRunTimestamp")
    # The date and time to which the prediction applies. Will most often be copied directly from
    # prediction_timestamp for the ModelRunGridSubsetPrediction, but is included again for cases
    # when values are interpolated (e.g., noon interpolations on GDPS model runs)
    prediction_timestamp = Column(TZTimeStamp, nullable=False)
    # Temperature 2m above model layer - an interpolated value based on 4 values from
    # model_run_grid_subset_prediction
    tmp_tgl_2 = Column(Float, nullable=True)
    # Temperature prediction using available data.
    bias_adjusted_temperature = Column(Float, nullable=True)
    # Relative Humidity 2m above model layer - an interpolated value based on 4 values
    # from model_run_grid_subset_prediction
    rh_tgl_2 = Column(Float, nullable=True)
    # RH adjusted by bias
    bias_adjusted_rh = Column(Float, nullable=True)
    # Accumulated precipitation over calendar day measured in UTC (units kg.m^-2)
    apcp_sfc_0 = Column(Float, nullable=True)
    # Change in accumulated precipitation between current and previous prediction_timestamp
    delta_precip = Column(Float, nullable=True)
    # Wind direction 10m above ground.
    wdir_tgl_10 = Column(Float, nullable=True)
    # Wind speed 10m above ground.
    wind_tgl_10 = Column(Float, nullable=True)
    # Date this record was created.
    create_date = Column(TZTimeStamp, nullable=False,
                         default=time_utils.get_utc_now())
    # Date this record was updated.
    update_date = Column(TZTimeStamp, nullable=False,
                         default=time_utils.get_utc_now())

    def __str__(self):
        return ('{self.station_code} {self.prediction_timestamp} {self.tmp_tgl_2} {self.apcp_sfc_0} '
                '{self.delta_precip}').format(self=self)
