""" Code for generating c-haines charts from grib files.

"""
# from typing import Final, List
# import os
# from datetime import datetime, timezone, timedelta
# import tempfile
# import json
# import logging
# import numpy
# import gdal
# import ogr
# from sqlalchemy.orm import Session
# from shapely.ops import transform
# from shapely.geometry import shape
# from pyproj import CRS, Transformer, Proj
# from app import configure_logging
# from app.weather_models import ModelEnum, ProjectionEnum
# from app.weather_models.process_grib import (get_transformer, GEO_CRS,
#                                              get_dataset_geometry, calculate_geographic_coordinate)
# from app.db.models import CHainesPoly, CHainesPrediction, CHainesModelRun
# from app.db.crud.weather_models import get_prediction_model
# from app.time_utils import get_utc_now
# from app.weather_models.env_canada import (get_model_run_hours,
#                                            get_file_date_part, adjust_model_day, download,
#                                            UnhandledPredictionModelType)
# import app.db.database
# from app.c_haines.severity_index import CHainesSeverityGenerator
