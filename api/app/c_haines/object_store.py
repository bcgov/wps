""" functions common to the object store
"""
import os
from enum import Enum
from datetime import datetime
from app.weather_models import ModelEnum


class ObjectTypeEnum(Enum):
    """ Types of object store files """
    KML = 'kml'
    GEOJSON = 'json'


def generate_object_store_filename(prediction_timestamp: datetime, object_type: ObjectTypeEnum) -> str:
    """ Generate the filename for a model run prediction """
    return f'{prediction_timestamp.isoformat()[:19]}.{object_type.value}'


def generate_full_object_store_path(prediction_model: ModelEnum,
                                    model_run_timestamp: datetime,
                                    prediction_timestamp: datetime,
                                    object_type: ObjectTypeEnum) -> str:
    """ Generate the path for a model run prediction. """

    object_filename = generate_object_store_filename(prediction_timestamp, object_type)
    model_run_path = generate_object_store_model_run_path(prediction_model, model_run_timestamp, object_type)

    return os.path.join(model_run_path, object_filename)


def generate_object_store_model_run_path(
        prediction_model: ModelEnum,
        model_run_timestamp: datetime,
        object_type: ObjectTypeEnum) -> str:
    """ Generate a path where model runs will be stored. """
    return os.path.join('c-haines-polygons',
                        object_type.value,
                        prediction_model.value,
                        f'{model_run_timestamp.year}',
                        f'{model_run_timestamp.month}',
                        f'{model_run_timestamp.day}',
                        f'{model_run_timestamp.hour}')
