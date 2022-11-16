""" Class models that reflect resources and map to database tables
"""
# Keep all the models in one place for alembic to discover:
from db.database import Base
from db.models.forecasts import NoonForecast
from db.models.observations import HourlyActual
from db.models.api_access_audits import APIAccessAudit
from db.models.weather_models import (ProcessedModelRunUrl, PredictionModel, PredictionModelRunTimestamp,
                                      PredictionModelGridSubset, ModelRunGridSubsetPrediction,
                                      WeatherStationModelPrediction)
from db.models.hfi_calc import (FireCentre, FuelType, PlanningArea, PlanningWeatherStation)
from db.models.auto_spatial_advisory import (Shape, ShapeType, HfiClassificationThreshold,
                                             ClassifiedHfi, RunTypeEnum, ShapeTypeEnum, FuelType)
