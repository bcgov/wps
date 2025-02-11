"""Class models that reflect resources and map to database tables"""

from sqlalchemy.ext.declarative import declarative_base

# Keep all the models in one place for alembic to discover:
# constructing a base class for declarative class definitions
Base = declarative_base()

from common.db.models.forecasts import NoonForecast
from common.db.models.observations import HourlyActual
from common.db.models.api_access_audits import APIAccessAudit
from common.db.models.weather_models import (
    ProcessedModelRunUrl,
    PredictionModel,
    PredictionModelRunTimestamp,
    PredictionModelGridSubset,
    ModelRunGridSubsetPrediction,
    WeatherStationModelPrediction,
    SavedModelRunForSFMSUrl,
    ModelRunForSFMS,
)
from common.db.models.hfi_calc import (
    FireCentre,
    FuelType,
    PlanningArea,
    PlanningWeatherStation,
)
from common.db.models.auto_spatial_advisory import (
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
)
from common.db.models.morecast_v2 import MorecastForecastRecord
from common.db.models.snow import ProcessedSnow, SnowSourceEnum
from common.db.models.grass_curing import PercentGrassCuring
