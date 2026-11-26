"""CRUD operations for the weather model records SFMS keeps: the RDPS grids it saves to object
storage, and the model runs those grids belong to.

Station predictions from the weather models are not in the database. They are in the `runs` and
`by_time` tables in object storage; see wps_weather_data.
"""

import datetime
import logging

from sqlalchemy.orm import Session

from wps_shared.db.models.weather_models import (
    ModelRunForSFMS,
    PredictionModel,
    SavedModelRunForSFMSUrl,
)
from wps_shared.utils.time import get_utc_now
from wps_shared.weather_models import ModelEnum

logger = logging.getLogger(__name__)


def get_saved_model_run_for_sfms(session: Session, url: str) -> SavedModelRunForSFMSUrl:
    """Get record corresponding to a processed model run url for sfms"""
    return session.query(SavedModelRunForSFMSUrl).filter(SavedModelRunForSFMSUrl.url == url).first()


def create_saved_model_run_for_sfms_url(session: Session, url: str, key: str):
    """Create a record of a model run url that has been downloaded and stored in S3."""
    now = get_utc_now()
    saved_model_run_for_sfms_url = SavedModelRunForSFMSUrl(
        url=url, create_date=now, update_date=now, s3_key=key
    )
    session.add(saved_model_run_for_sfms_url)
    session.commit()


def get_rdps_sfms_urls_for_deletion(session: Session, threshold: datetime):
    """Gets all records older than the provided threshold."""
    return (
        session.query(SavedModelRunForSFMSUrl)
        .filter(SavedModelRunForSFMSUrl.create_date < threshold)
        .all()
    )


def delete_rdps_sfms_urls(session: Session, ids: list[int]):
    """Delete records with the specified ids."""
    if ids is not None and len(ids) > 0:
        session.query(SavedModelRunForSFMSUrl).filter(SavedModelRunForSFMSUrl.id.in_(ids)).delete()


def create_model_run_for_sfms(
    session: Session, model: ModelEnum, model_run_date: datetime, model_run_hour: int
):
    """Create a model run for sfms record to indicate that weather model data for the given
    date and model has been stored in S3.
    """
    prediction_model = get_prediction_model_by_model_enum(session, model)
    model_run_timestamp = datetime.datetime(
        year=model_run_date.year,
        month=model_run_date.month,
        day=model_run_date.day,
        hour=model_run_hour,
        tzinfo=datetime.timezone.utc,
    )
    model_run_for_sfms = ModelRunForSFMS(
        prediction_model_id=prediction_model.id,
        model_run_timestamp=model_run_timestamp,
        create_date=model_run_date,
        update_date=model_run_date,
    )
    session.add(model_run_for_sfms)
    session.commit()


def get_prediction_model_by_model_enum(session: Session, model_enum: ModelEnum):
    """Get the PredictionModel corresponding to a particular model enum."""
    return (
        session.query(PredictionModel)
        .filter(PredictionModel.abbreviation == model_enum.value)
        .first()
    )
