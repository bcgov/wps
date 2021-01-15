""" Class models that reflect resources and map to database tables
"""
# Keep all the models in one place for alembic to discover:
from app.db.database import Base
from app.db.models.forecasts import NoonForecast
from app.db.models.observations import HourlyActual
from app.db.models.weather_models import (ProcessedModelRunUrl, PredictionModel, PredictionModelRunTimestamp,
                                          PredictionModelGridSubset, ModelRunGridSubsetPrediction,
                                          WeatherStationModelPrediction, CHainesPoly)
