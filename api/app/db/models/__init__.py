""" Class models that reflect resources and map to database tables
"""
from sqlalchemy.ext.declarative import declarative_base

# Keep all the models in one place for alembic to discover:
# constructing a base class for declarative class definitions
Base = declarative_base()

from app.db.models.forecasts import NoonForecast
from app.db.models.observations import HourlyActual
from app.db.models.api_access_audits import APIAccessAudit
from app.db.models.weather_models import (ProcessedModelRunUrl, PredictionModel, PredictionModelRunTimestamp,
                                          PredictionModelGridSubset, ModelRunGridSubsetPrediction,
                                          WeatherStationModelPrediction)
from app.db.models.hfi_calc import (FireCentre, FuelType, PlanningArea, PlanningWeatherStation)
from app.db.models.auto_spatial_advisory import (Shape, ShapeType, HfiClassificationThreshold,
                                                 ClassifiedHfi, RunTypeEnum, ShapeTypeEnum, FuelType, HighHfiArea, RunParameters)
