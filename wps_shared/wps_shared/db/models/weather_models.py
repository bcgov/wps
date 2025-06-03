"""Class models that reflect resources and map to database tables relating to weather models."""

import logging
import numpy as np
from sqlalchemy import Column, String, Integer, Float, Boolean, Sequence, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from geoalchemy2 import Geometry
from wps_shared.db.models import Base
import wps_shared.utils.time as time_utils
from wps_shared.db.models.common import TZTimeStamp

logger = logging.getLogger(__name__)


class ProcessedModelRunUrl(Base):
    """Record to indicate that a particular model run file has been processed.
    NOTE: One could check if values for a particular model run exists, but that would make it more
    difficult to re-process files as you'd have to delete existing values.
    """

    __tablename__ = "processed_model_run_urls"
    __table_args__ = {"comment": "Record to indicate that a particular model run file has been processed."}
    # Unique identifier.
    id = Column(Integer, Sequence("processed_model_run_url_id_seq"), primary_key=True, nullable=False, index=True)
    # Source URL of file processed.
    url = Column(String, nullable=False, unique=True, index=True)
    # Date this record was created.
    create_date = Column(TZTimeStamp, nullable=False)
    # Date this record was updated.
    update_date = Column(TZTimeStamp, nullable=False)


class SavedModelRunForSFMSUrl(Base):
    """Record to indicate that a particular RDPS model run file has been downloaded
    and saved to S3 storage.
    """

    __tablename__ = "saved_model_run_for_sfms_urls"
    __table_args__ = {"comment": "Record to indicate that a particular RDPS model run file has been downloaded and saved to S3 storage."}
    # Unique identifier.
    id = Column(Integer, Sequence("saved_model_run_for_sfms_urls_id_seq"), primary_key=True, nullable=False, index=True)
    # Source URL of file processed.
    url = Column(String, nullable=False, unique=True, index=True)
    # The S3 key for the downloaded data
    s3_key = Column(String, nullable=False, unique=True, index=True)
    # Date this record was created.
    create_date = Column(TZTimeStamp, nullable=False)
    # Date this record was updated.
    update_date = Column(TZTimeStamp, nullable=False)


class ModelRunForSFMS(Base):
    """Record to indicate numerical weather model data for SFMS has been downloaded and stored in S3."""

    __tablename__ = "model_run_for_sfms"
    __table_args__ = {"comment": "Record to indicate numerical weather model data for SFMS has been downloaded and stored in S3."}
    # Unique identifier.
    id = Column(Integer, Sequence("model_run_for_sfms_id_seq"), primary_key=True, nullable=False, index=True)
    # The numerical weather model.
    prediction_model_id = Column(Integer, ForeignKey("prediction_models.id"), nullable=False)
    prediction_model = relationship("PredictionModel")
    # The date and time of the model run.
    model_run_timestamp = Column(TZTimeStamp, nullable=False, index=True)
    # Date this record was created.
    create_date = Column(TZTimeStamp, nullable=False)
    # Date this record was updated.
    update_date = Column(TZTimeStamp, nullable=False)


class PredictionModel(Base):
    """Identifies the Weather Prediction model (e.g. GDPS 15km resolution)."""

    __tablename__ = "prediction_models"
    __table_args__ = (UniqueConstraint("abbreviation", "projection"), {"comment": "Identifies the Weather Prediction model"})

    id = Column(Integer, Sequence("prediction_models_id_seq"), primary_key=True, nullable=False, index=True)
    # E.g. Global Deterministic Prediction System
    name = Column(String, nullable=False)
    # E.g. GDPS
    abbreviation = Column(String, nullable=False, index=True)
    # E.g. latlon.15x15
    # NOTE: we may want to consider not bothering with projection, since we would store it as geopgraphical
    # regardles. A better approach may be to just store the resolution: "15x15"
    projection = Column(String, nullable=False)

    def __str__(self):
        return "id:{self.id}, name:{self.name}, abbreviation:{self.abbreviation}, projection:{self.projection}".format(self=self)


class PredictionModelRunTimestamp(Base):
    """Identify which prediction model run (e.g.  2020 07 07 12:00)."""

    __tablename__ = "prediction_model_run_timestamps"
    __table_args__ = (UniqueConstraint("prediction_model_id", "prediction_run_timestamp"), {"comment": "Identify which prediction model run (e.g.  2020 07 07 12:00)."})

    id = Column(Integer, Sequence("prediction_model_run_timestamps_id_seq"), primary_key=True, nullable=False, index=True)
    # The numerical weather model.
    prediction_model_id = Column(Integer, ForeignKey("prediction_models.id"), nullable=False, index=True)
    prediction_model = relationship("PredictionModel")
    # The date and time of the model run.
    prediction_run_timestamp = Column(TZTimeStamp, nullable=False, index=True)
    # Indicate if this particular model run is completely downloaded.
    complete = Column(Boolean, nullable=False)
    # Indicate if this model run has been interpolated for weather stations.
    interpolated = Column(Boolean, nullable=False)

    def __str__(self):
        return (
            "id:{self.id}, "
            "prediction_model:{self.prediction_model.abbreviation}:{self.prediction_model.projection}, "
            "prediction_run_timestamp:{self.prediction_run_timestamp}, "
            "complete={self.complete}"
        ).format(self=self)


class PredictionModelGridSubset(Base):
    """Identify the vertices surrounding the area of interest"""

    __tablename__ = "prediction_model_grid_subsets"
    __table_args__ = (UniqueConstraint("prediction_model_id", "geom"), {"comment": "Identify the vertices surrounding the area of interest"})

    id = Column(Integer, Sequence("prediction_model_grid_subsets_id_seq"), primary_key=True, nullable=False, index=True)
    # Which model does this grid belong to? e.g. GDPS latlon.15x.15?
    prediction_model_id = Column(Integer, ForeignKey("prediction_models.id"), nullable=False, index=True)
    prediction_model = relationship("PredictionModel")
    # Order of vertices is important!
    # 1st vertex top left, 2nd vertex top right, 3rd vertex bottom right, 4th vertex bottom left.
    # We create the index later, due to issue with alembic + geoalchemy.
    geom = Column(Geometry("POLYGON", spatial_index=False), nullable=False)

    def __str__(self):
        return ("id: {self.id}, prediction_model_id: {self.prediction_model_id}").format(self=self)


# Explicit creation of index due to issue with alembic + geoalchemy.
Index("idx_prediction_model_grid_subsets_geom", PredictionModelGridSubset.geom, postgresql_using="gist")


class ModelRunGridSubsetPrediction(Base):
    """The prediction for a particular model grid subset.
    Each value is an array that corresponds to the vertex in the prediction bounding polygon."""

    __tablename__ = "model_run_grid_subset_predictions"
    __table_args__ = (
        UniqueConstraint("prediction_model_run_timestamp_id", "prediction_model_grid_subset_id", "prediction_timestamp"),
        {"comment": "The prediction for a grid subset of a particular model run."},
    )

    id = Column(Integer, Sequence("model_run_grid_subset_predictions_id_seq"), primary_key=True, nullable=False, index=True)
    # Which model run does this forecacst apply to? E.g. The GDPS 15x.15 run from 2020 07 07 12h00.
    prediction_model_run_timestamp_id = Column(Integer, ForeignKey("prediction_model_run_timestamps.id"), nullable=False, index=True)
    prediction_model_run_timestamp = relationship("PredictionModelRunTimestamp", foreign_keys=[prediction_model_run_timestamp_id])
    # Which grid does this prediction apply to?
    prediction_model_grid_subset_id = Column(Integer, ForeignKey("prediction_model_grid_subsets.id"), nullable=False, index=True)
    prediction_model_grid_subset = relationship("PredictionModelGridSubset")
    # The date and time to which the prediction applies.
    prediction_timestamp = Column(TZTimeStamp, nullable=False, index=True)
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
        return (
            "id:{self.id}, "
            "prediction_model_run_timestamp_id:{self.prediction_model_run_timestamp_id}, "
            "prediction_model_grid_subset_id:{self.prediction_model_grid_subset_id}, "
            "prediction_timestamp={self.prediction_timestamp}, "
            "tmp_tgl_2={self.tmp_tgl_2}, "
            "rh_tgl_2={self.rh_tgl_2}, "
            "apcp_sfc_0={self.apcp_sfc_0}, "
            "wdir_tgl_10={self.wdir_tgl_10}, "
        ).format(self=self)


class ModelRunPrediction(Base):
    """The prediction for a particular model.
    Each value is a numeric value that corresponds to the lat lon from the model raster"""

    __tablename__ = "model_run_predictions"
    __table_args__ = (UniqueConstraint("prediction_model_run_timestamp_id", "prediction_timestamp", "station_code"), {"comment": "The prediction values of a particular model run."})

    id = Column(Integer, Sequence("model_run_predictions_id_seq"), primary_key=True, nullable=False, index=True)
    # Which model run does this forecacst apply to? E.g. The GDPS 15x.15 run from 2020 07 07 12h00.
    prediction_model_run_timestamp_id = Column(Integer, ForeignKey("prediction_model_run_timestamps.id"), nullable=False, index=True)
    prediction_model_run_timestamp = relationship("PredictionModelRunTimestamp", foreign_keys=[prediction_model_run_timestamp_id])
    # The date and time to which the prediction applies.
    prediction_timestamp = Column(TZTimeStamp, nullable=False, index=True)
    # The station code representing the location (aka weather station).
    station_code = Column(Integer, nullable=False)
    # Temperature 2m above model layer.
    tmp_tgl_2 = Column(Float, nullable=True)
    # Relative humidity 2m above model layer.
    rh_tgl_2 = Column(Float, nullable=True)
    # Accumulated precipitation (units kg.m^-2)
    apcp_sfc_0 = Column(Float, nullable=True)
    # Wind direction 10m above ground.
    wdir_tgl_10 = Column(Float, nullable=True)
    # Wind speed 10m above ground.
    wind_tgl_10 = Column(Float, nullable=True)

    def _get_field_value(self, field_name: str, field_value: float | np.float64 | None) -> float | None:
        """Helper method to process field values."""
        value = field_value.item() if isinstance(field_value, np.float64) else field_value
        if value is None:
            logger.warning(f"{field_name} is None for ModelRunPrediction.id == %s", self.id)
        return value

    def get_temp(self) -> float | None:
        return self._get_field_value(ModelRunPrediction.tmp_tgl_2.name, self.tmp_tgl_2)

    def get_rh(self) -> float | None:
        return self._get_field_value(ModelRunPrediction.rh_tgl_2.name, self.rh_tgl_2)
    
    def get_precip(self) -> float | None:
        precip = self._get_field_value(ModelRunPrediction.apcp_sfc_0.name, self.apcp_sfc_0)
        return precip if precip is not None else 0.0
    
    def get_wind_speed(self) -> float | None:
        return self._get_field_value(ModelRunPrediction.wind_tgl_10.name, self.wind_tgl_10)
    
    def get_wind_direction(self) -> float | None:
        return self._get_field_value(ModelRunPrediction.wdir_tgl_10.name, self.wdir_tgl_10)

    @staticmethod
    def get_weather_model_fields():
        """Return the list of weather model fields as direct references."""
        return [
            ModelRunPrediction.tmp_tgl_2.name,
            ModelRunPrediction.rh_tgl_2.name,
            ModelRunPrediction.apcp_sfc_0.name,
            ModelRunPrediction.wdir_tgl_10.name,
            ModelRunPrediction.wind_tgl_10.name,
        ]


class WeatherStationModelPrediction(Base):
    """The model prediction for a particular weather station.
    Based on values from ModelRunGridSubsetPrediction, but captures linear interpolations based on weather
    station's location within the grid_subset, and also captures time-based linear interpolations where
    needed for certain Model types."""

    __tablename__ = "weather_station_model_predictions"
    __table_args__ = (
        UniqueConstraint("station_code", "prediction_model_run_timestamp_id", "prediction_timestamp"),
        {"comment": "The interpolated weather values for a weather station, weather date, and model run"},
    )

    id = Column(Integer, Sequence("weather_station_model_predictions_id_seq"), primary_key=True, nullable=False, index=True)
    # The 3-digit code for the weather station to which the prediction applies
    station_code = Column(Integer, nullable=False, index=True)
    # Which PredictionModelRunTimestamp is this station's prediction based on?
    prediction_model_run_timestamp_id = Column(Integer, ForeignKey("prediction_model_run_timestamps.id"), nullable=False, index=True)
    prediction_model_run_timestamp = relationship("PredictionModelRunTimestamp")
    # The date and time to which the prediction applies. Will most often be copied directly from
    # prediction_timestamp for the ModelRunGridSubsetPrediction, but is included again for cases
    # when values are interpolated (e.g., noon interpolations on GDPS model runs)
    prediction_timestamp = Column(TZTimeStamp, nullable=False, index=True)
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
    # Wind direction adjusted for bias
    bias_adjusted_wdir = Column(Float, nullable=True)
    # Wind speed 10m above ground.
    wind_tgl_10 = Column(Float, nullable=True)
    # Wind speed adjusted for bias
    bias_adjusted_wind_speed = Column(Float, nullable=True)
    # Date this record was created.
    create_date = Column(TZTimeStamp, nullable=False, default=time_utils.get_utc_now())
    # Date this record was updated.
    update_date = Column(TZTimeStamp, nullable=False, default=time_utils.get_utc_now(), index=True)
    # Precipitation predicted for the previous 24 hour period.
    precip_24h = Column(Float, nullable=True)
    # Precipitation predicted for the previous 24 hour period adjusted for bias.
    bias_adjusted_precip_24h = Column(Float, nullable=True)

    def __str__(self):
        return (
            "{self.station_code} {self.prediction_timestamp} {self.tmp_tgl_2} {self.bias_adjusted_temperature} "
            "{self.rh_tgl_2} {self.bias_adjusted_rh} {self.wdir_tgl_10} {self.bias_adjusted_wdir} {self.wind_tgl_10} "
            "{self.bias_adjusted_wind_speed} {self.apcp_sfc_0} {self.delta_precip} {self.bias_adjusted_precip_24h}"
        ).format(self=self)


class MoreCast2MaterializedView(Base):
    """A materialized view to support efficient retrieval of weather model prediction data by
    stations and dates."""

    __tablename__ = "morecast_2_materialized_view"
    id = Column(Integer, Sequence("morecast_forecast_id_seq"), primary_key=True, nullable=False, index=True)
    abbreviation = Column(String, nullable=False)
    apcp_sfc_0 = Column(Float, nullable=False)
    bias_adjusted_precip_24h = Column(Float, nullable=False)
    bias_adjusted_rh = Column(Float, nullable=False)
    bias_adjusted_temperature = Column(Float, nullable=False)
    bias_adjusted_wind_speed = Column(Float, nullable=False)
    bias_adjusted_wdir = Column(Float, nullable=False)
    precip_24h = Column(Float, nullable=False)
    prediction_timestamp = Column(TZTimeStamp, nullable=False, index=True)
    station_code = Column(Integer, nullable=True, index=True)
    rh_tgl_2 = Column(Float, nullable=False)
    tmp_tgl_2 = Column(Float, nullable=False)
    update_date = Column(TZTimeStamp, nullable=False, index=True)
    wdir_tgl_10 = Column(Float, nullable=False)
    wind_tgl_10 = Column(Float, nullable=False)
