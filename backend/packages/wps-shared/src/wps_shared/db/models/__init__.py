"""Class models that reflect resources and map to database tables"""
# ruff: noqa

from sqlalchemy.ext.declarative import declarative_base

# Keep all the models in one place for alembic to discover:
# constructing a base class for declarative class definitions
Base = declarative_base()

from wps_shared.db.models.forecasts import NoonForecast
from wps_shared.db.models.observations import HourlyActual
from wps_shared.db.models.api_access_audits import APIAccessAudit
from wps_shared.db.models.weather_models import (
    ProcessedModelRunUrl,
    PredictionModel,
    PredictionModelRunTimestamp,
    PredictionModelGridSubset,
    ModelRunGridSubsetPrediction,
    WeatherStationModelPrediction,
    SavedModelRunForSFMSUrl,
    ModelRunForSFMS,
)
from wps_shared.db.models.hfi_calc import FireCentre, FuelType, PlanningArea, PlanningWeatherStation
from wps_shared.db.models.auto_spatial_advisory import (
    Shape,
    ShapeType,
    HfiClassificationThreshold,
    ClassifiedHfi,
    RunTypeEnum,
    ShapeTypeEnum,
    FuelType,
    HighHfiArea,
    RunParameters,
    CriticalHours,
    AdvisoryHFIWindSpeed,
)
from wps_shared.db.models.morecast_v2 import MorecastForecastRecord
from wps_shared.db.models.snow import ProcessedSnow, SnowSourceEnum
from wps_shared.db.models.grass_curing import PercentGrassCuring
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.db.models.fire_watch import FireWatch, FireWatchWeather, PrescriptionStatus
from wps_shared.db.models.sfms_run import SFMSRunLog
