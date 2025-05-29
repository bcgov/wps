"""CRUD operations for management of weather model data."""

import logging
import datetime
from typing import List, Union
from sqlalchemy import and_, extract, func, select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.schemas.weather_models import ModelPredictionDetails
from wps_shared.weather_models import ModelEnum, ProjectionEnum
from wps_shared.db.models.weather_models import (
    ProcessedModelRunUrl,
    PredictionModel,
    PredictionModelRunTimestamp,
    ModelRunPrediction,
    WeatherStationModelPrediction,
    SavedModelRunForSFMSUrl,
    ModelRunForSFMS,
)
from wps_shared.utils.time import get_utc_now

logger = logging.getLogger(__name__)


def get_prediction_run(
    session: Session, prediction_model_id: int, prediction_run_timestamp: datetime.datetime
) -> PredictionModelRunTimestamp:
    """load the model run from the database (.e.g. for 2020 07 07 12h00)."""
    logger.info("get prediction run for %s", prediction_run_timestamp)
    return (
        session.query(PredictionModelRunTimestamp)
        .filter(PredictionModelRunTimestamp.prediction_model_id == prediction_model_id)
        .filter(PredictionModelRunTimestamp.prediction_run_timestamp == prediction_run_timestamp)
        .first()
    )


def create_prediction_run(
    session: Session,
    prediction_model_id: int,
    prediction_run_timestamp: datetime.datetime,
    complete: bool,
    interpolated: bool,
) -> PredictionModelRunTimestamp:
    """Create a model prediction run for a particular model."""
    prediction_run = PredictionModelRunTimestamp(
        prediction_model_id=prediction_model_id,
        prediction_run_timestamp=prediction_run_timestamp,
        complete=complete,
        interpolated=interpolated,
    )
    session.add(prediction_run)
    session.commit()
    return prediction_run


def update_prediction_run(session: Session, prediction_run: PredictionModelRunTimestamp):
    """Update a PredictionModelRunTimestamp record"""
    session.add(prediction_run)
    session.commit()


def get_or_create_prediction_run(
    session, prediction_model: PredictionModel, prediction_run_timestamp: datetime.datetime
) -> PredictionModelRunTimestamp:
    """Get a model prediction run for a particular model, creating one if it doesn't already exist."""
    prediction_run = get_prediction_run(session, prediction_model.id, prediction_run_timestamp)
    if not prediction_run:
        logger.info(
            "Creating prediction run %s for %s",
            prediction_model.abbreviation,
            prediction_run_timestamp,
        )
        prediction_run = create_prediction_run(
            session, prediction_model.id, prediction_run_timestamp, False, False
        )
    return prediction_run


def get_model_run_predictions_for_station(
    session: Session, station_code: int, prediction_run: PredictionModelRunTimestamp
) -> List:
    """Get all the predictions for a provided model run"""
    logger.info("Getting model predictions for grid %s", prediction_run)
    return (
        session.query(ModelRunPrediction)
        .filter(ModelRunPrediction.prediction_model_run_timestamp_id == prediction_run.id)
        .filter(ModelRunPrediction.station_code == station_code)
        .order_by(ModelRunPrediction.prediction_timestamp)
    )


def delete_model_run_predictions(session: Session, older_than: datetime):
    """Delete any model run prediction older than a certain date."""
    logger.info("Deleting model_run_prediction data older than %s...", older_than)
    session.query(ModelRunPrediction).filter(
        ModelRunPrediction.prediction_timestamp < older_than
    ).delete()


def get_station_model_predictions_order_by_prediction_timestamp(
    session: Session,
    station_codes: List,
    model: ModelEnum,
    start_date: datetime.datetime,
    end_date: datetime.datetime,
) -> List[Union[WeatherStationModelPrediction, PredictionModel]]:
    """Fetch model predictions for given stations within given time range ordered by station code
    and prediction timestamp.

    This is useful if you're interested in seeing all the different predictions regardles of
    model run.
    """
    query = (
        session.query(WeatherStationModelPrediction, PredictionModel)
        .join(
            PredictionModelRunTimestamp,
            PredictionModelRunTimestamp.id
            == WeatherStationModelPrediction.prediction_model_run_timestamp_id,
        )
        .join(
            PredictionModel, PredictionModel.id == PredictionModelRunTimestamp.prediction_model_id
        )
        .filter(WeatherStationModelPrediction.station_code.in_(station_codes))
        .filter(WeatherStationModelPrediction.prediction_timestamp >= start_date)
        .filter(WeatherStationModelPrediction.prediction_timestamp <= end_date)
        .filter(PredictionModel.abbreviation == model)
        .order_by(WeatherStationModelPrediction.station_code)
        .order_by(WeatherStationModelPrediction.prediction_timestamp)
    )
    return query


def get_station_model_predictions(
    session: Session,
    station_codes: List,
    model: str,
    start_date: datetime.datetime,
    end_date: datetime.datetime,
) -> List[Union[WeatherStationModelPrediction, PredictionModelRunTimestamp, PredictionModel]]:
    """Fetches the model predictions that were most recently issued before the prediction_timestamp.
    Used to compare the most recent model predictions against forecasts and actuals for the same
    weather date and weather station.
    Only fetches WeatherStationModelPredictions for prediction_timestamps in the date range of
    start_date - end_date (inclusive).
    """
    query = (
        session.query(WeatherStationModelPrediction, PredictionModelRunTimestamp, PredictionModel)
        .filter(WeatherStationModelPrediction.station_code.in_(station_codes))
        .filter(WeatherStationModelPrediction.prediction_timestamp >= start_date)
        .filter(WeatherStationModelPrediction.prediction_timestamp <= end_date)
        .filter(
            PredictionModelRunTimestamp.id
            == WeatherStationModelPrediction.prediction_model_run_timestamp_id
        )
        .filter(
            PredictionModelRunTimestamp.prediction_model_id == PredictionModel.id,
            PredictionModel.abbreviation == model,
        )
        .order_by(WeatherStationModelPrediction.station_code)
        .order_by(WeatherStationModelPrediction.prediction_timestamp)
        .order_by(PredictionModelRunTimestamp.prediction_run_timestamp.asc())
    )
    return query


def get_latest_station_model_prediction_per_day(
    session: Session,
    station_codes: List[int],
    model: str,
    day_start: datetime.datetime,
    day_end: datetime.datetime,
):
    """
    All weather station model predictions for:
     - a given day
     - a given model
     - each station in the given list
    ordered by update_timestamp

    This is done by joining the predictions on their runs,
    that are filtered by the day and the 20:00UTC predictions.

    In turn prediction runs are filtered via a join
    on runs that are for the selected model.
    """
    subquery = (
        session.query(
            func.max(WeatherStationModelPrediction.prediction_timestamp).label("latest_prediction"),
            WeatherStationModelPrediction.station_code,
            func.date(WeatherStationModelPrediction.prediction_timestamp).label("unique_day"),
        )
        .filter(
            WeatherStationModelPrediction.station_code.in_(station_codes),
            WeatherStationModelPrediction.prediction_timestamp >= day_start,
            WeatherStationModelPrediction.prediction_timestamp <= day_end,
            func.date_part("hour", WeatherStationModelPrediction.prediction_timestamp) == 20,
        )
        .group_by(
            WeatherStationModelPrediction.station_code,
            func.date(WeatherStationModelPrediction.prediction_timestamp).label("unique_day"),
        )
        .subquery("latest")
    )

    result = (
        session.query(
            WeatherStationModelPrediction.id,
            WeatherStationModelPrediction.prediction_timestamp,
            PredictionModel.abbreviation,
            WeatherStationModelPrediction.station_code,
            WeatherStationModelPrediction.rh_tgl_2,
            WeatherStationModelPrediction.tmp_tgl_2,
            WeatherStationModelPrediction.bias_adjusted_temperature,
            WeatherStationModelPrediction.bias_adjusted_rh,
            WeatherStationModelPrediction.apcp_sfc_0,
            WeatherStationModelPrediction.wdir_tgl_10,
            WeatherStationModelPrediction.wind_tgl_10,
            WeatherStationModelPrediction.update_date,
        )
        .join(
            PredictionModelRunTimestamp,
            WeatherStationModelPrediction.prediction_model_run_timestamp_id
            == PredictionModelRunTimestamp.id,
        )
        .join(
            PredictionModel, PredictionModelRunTimestamp.prediction_model_id == PredictionModel.id
        )
        .join(
            subquery,
            and_(
                WeatherStationModelPrediction.prediction_timestamp == subquery.c.latest_prediction,
                WeatherStationModelPrediction.station_code == subquery.c.station_code,
            ),
        )
        .filter(PredictionModel.abbreviation == model)
        .order_by(WeatherStationModelPrediction.update_date.desc())
    )
    return result


def get_latest_station_prediction(
    session: Session,
    station_codes: List[int],
    day_start: datetime.datetime,
    day_end: datetime.datetime,
):
    logger.info("Getting data from weather_station_model_predictions.")

    latest_predictions_subquery = (
        session.query(
            func.max(WeatherStationModelPrediction.prediction_timestamp).label("latest_prediction"),
            WeatherStationModelPrediction.station_code,
            func.date(WeatherStationModelPrediction.prediction_timestamp).label("unique_day"),
        )
        .filter(
            extract("hour", WeatherStationModelPrediction.prediction_timestamp) == 20,
            WeatherStationModelPrediction.station_code.in_(station_codes),
            WeatherStationModelPrediction.prediction_timestamp >= day_start,
            WeatherStationModelPrediction.prediction_timestamp <= day_end,
        )
        .group_by(
            WeatherStationModelPrediction.station_code,
            func.date(WeatherStationModelPrediction.prediction_timestamp),
        )
        .subquery()
    )

    result = (
        session.query(
            WeatherStationModelPrediction.prediction_timestamp,
            PredictionModel.abbreviation,
            WeatherStationModelPrediction.station_code,
            WeatherStationModelPrediction.rh_tgl_2,
            WeatherStationModelPrediction.tmp_tgl_2,
            WeatherStationModelPrediction.bias_adjusted_temperature,
            WeatherStationModelPrediction.bias_adjusted_rh,
            WeatherStationModelPrediction.bias_adjusted_wind_speed,
            WeatherStationModelPrediction.bias_adjusted_wdir,
            WeatherStationModelPrediction.precip_24h,
            WeatherStationModelPrediction.bias_adjusted_precip_24h,
            WeatherStationModelPrediction.wdir_tgl_10,
            WeatherStationModelPrediction.wind_tgl_10,
        )
        .join(
            PredictionModelRunTimestamp,
            PredictionModelRunTimestamp.id
            == WeatherStationModelPrediction.prediction_model_run_timestamp_id,
        )
        .join(
            PredictionModel, PredictionModel.id == PredictionModelRunTimestamp.prediction_model_id
        )
        .join(
            latest_predictions_subquery,
            (
                WeatherStationModelPrediction.prediction_timestamp
                == latest_predictions_subquery.c.latest_prediction
            )
            & (
                WeatherStationModelPrediction.station_code
                == latest_predictions_subquery.c.station_code
            ),
        )
        .order_by(WeatherStationModelPrediction.update_date.desc())
    )

    return result


async def get_latest_model_prediction_for_stations(
    session: Session,
    station_codes: list[int],
    model: ModelEnum,
    day_start: datetime.datetime,
    day_end: datetime.datetime,
) -> list[ModelPredictionDetails]:
    """
    Retrieves the most recent model predictions for each station and day, ensuring that only
    predictions with a timestamp at 20:00 hours are included. The results are distinct by prediction date and station code.
    The DISTINCT ON clause is used to ensure that only the latest prediction (by update_date) for each station and day is returned.
    Note: DISTINCT ON only works with PostgreSQL.

    :param session: SQLAlchemy session used to execute the query.
    :param station_codes: List of station codes to filter the predictions.
    :param model: Weather prediction model to filter by.
    :param day_start: Start of the time range for predictions.
    :param day_end: End of the time range for predictions.
    :return: List of the latest model prediction details for each station and day.

    """
    stmt = (
        select(
            WeatherStationModelPrediction.prediction_timestamp,
            WeatherStationModelPrediction.update_date,
            PredictionModel.abbreviation,
            PredictionModelRunTimestamp.prediction_run_timestamp,
            WeatherStationModelPrediction.prediction_model_run_timestamp_id,
            WeatherStationModelPrediction.station_code,
            WeatherStationModelPrediction.rh_tgl_2,
            WeatherStationModelPrediction.tmp_tgl_2,
            WeatherStationModelPrediction.bias_adjusted_temperature,
            WeatherStationModelPrediction.bias_adjusted_rh,
            WeatherStationModelPrediction.bias_adjusted_wind_speed,
            WeatherStationModelPrediction.bias_adjusted_wdir,
            WeatherStationModelPrediction.precip_24h,
            WeatherStationModelPrediction.bias_adjusted_precip_24h,
            WeatherStationModelPrediction.wdir_tgl_10,
            WeatherStationModelPrediction.wind_tgl_10,
        )
        .join(
            PredictionModelRunTimestamp,
            WeatherStationModelPrediction.prediction_model_run_timestamp_id
            == PredictionModelRunTimestamp.id,
        )
        .join(
            PredictionModel, PredictionModel.id == PredictionModelRunTimestamp.prediction_model_id
        )
        .where(
            extract("hour", WeatherStationModelPrediction.prediction_timestamp) == 20,
            WeatherStationModelPrediction.station_code.in_(station_codes),
            WeatherStationModelPrediction.prediction_timestamp.between(day_start, day_end),
            PredictionModelRunTimestamp.interpolated == True,
            PredictionModel.abbreviation == model.value,
        )
        .distinct(
            func.date(WeatherStationModelPrediction.prediction_timestamp),
            WeatherStationModelPrediction.station_code,
        )
        .order_by(
            WeatherStationModelPrediction.station_code,
            func.date(WeatherStationModelPrediction.prediction_timestamp),
            PredictionModelRunTimestamp.prediction_run_timestamp.desc(),
        )
    )
    results = await session.execute(stmt)
    latest_predictions = [ModelPredictionDetails(**row) for row in results.mappings().all()]

    return latest_predictions


def get_station_model_prediction_from_previous_model_run(
    session: Session,
    station_code: int,
    model: ModelEnum,
    prediction_timestamp: datetime.datetime,
    prediction_model_run_timestamp: datetime.datetime,
) -> List[WeatherStationModelPrediction]:
    """Fetches the one model prediction for the specified station_code, model, and prediction_timestamp
    from the prediction model run immediately previous to the given prediction_model_run_timestamp.
    """
    # create a lower_bound for time range so that we're not querying timestamps all the way back to the
    # beginning of time
    lower_bound = prediction_model_run_timestamp - datetime.timedelta(days=1)
    response = (
        session.query(WeatherStationModelPrediction)
        .join(
            PredictionModelRunTimestamp,
            PredictionModelRunTimestamp.id
            == WeatherStationModelPrediction.prediction_model_run_timestamp_id,
        )
        .join(
            PredictionModel, PredictionModel.id == PredictionModelRunTimestamp.prediction_model_id
        )
        .filter(WeatherStationModelPrediction.station_code == station_code)
        .filter(WeatherStationModelPrediction.prediction_timestamp == prediction_timestamp)
        .filter(PredictionModel.abbreviation == model)
        .filter(
            PredictionModelRunTimestamp.prediction_run_timestamp < prediction_model_run_timestamp
        )
        .filter(PredictionModelRunTimestamp.prediction_run_timestamp > lower_bound)
        .order_by(PredictionModelRunTimestamp.prediction_run_timestamp.desc())
        .limit(1)
        .first()
    )

    return response


def get_processed_file_count(session: Session, urls: List[str]) -> int:
    """Return the number of matching urls"""
    return session.query(ProcessedModelRunUrl).filter(ProcessedModelRunUrl.url.in_(urls)).count()


def get_processed_file_record(session: Session, url: str) -> ProcessedModelRunUrl:
    """Get record corresponding to a processed file."""
    processed_file = (
        session.query(ProcessedModelRunUrl).filter(ProcessedModelRunUrl.url == url).first()
    )
    return processed_file


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


def get_prediction_model(
    session: Session, model_enum: ModelEnum, projection: ProjectionEnum
) -> PredictionModel:
    """Get the prediction model corresponding to a particular abbreviation and projection."""
    return (
        session.query(PredictionModel)
        .filter(PredictionModel.abbreviation == model_enum.value)
        .filter(PredictionModel.projection == projection.value)
        .first()
    )


def get_prediction_model_run_timestamp_records(
    session: Session, model_type: ModelEnum, complete: bool = True, interpolated: bool = True
):
    """Get prediction model run timestamps (filter on complete and interpolated if provided.)"""
    query = (
        session.query(PredictionModelRunTimestamp, PredictionModel)
        .join(
            PredictionModelRunTimestamp,
            PredictionModelRunTimestamp.prediction_model_id == PredictionModel.id,
        )
        .filter(PredictionModel.abbreviation == model_type.value)
    )
    if interpolated is not None:
        query = query.filter(PredictionModelRunTimestamp.interpolated == interpolated)
    if complete is not None:
        query = query.filter(PredictionModelRunTimestamp.complete == complete)
    query = query.order_by(PredictionModelRunTimestamp.prediction_run_timestamp)
    return query


def get_weather_station_model_prediction(
    session: Session,
    station_code: int,
    prediction_model_run_timestamp_id: int,
    prediction_timestamp: datetime,
) -> WeatherStationModelPrediction:
    """Get the model prediction for a weather station given a model run and a timestamp."""
    return (
        session.query(WeatherStationModelPrediction)
        .filter(WeatherStationModelPrediction.station_code == station_code)
        .filter(
            WeatherStationModelPrediction.prediction_model_run_timestamp_id
            == prediction_model_run_timestamp_id
        )
        .filter(WeatherStationModelPrediction.prediction_timestamp == prediction_timestamp)
        .first()
    )


async def get_latest_prediction_timestamp_id_for_model(
    session: AsyncSession, model: ModelEnum
) -> int:
    """Get the latest prediction model run timestamp id for a given model."""

    stmt = (
        select(PredictionModelRunTimestamp.id)
        .join(
            PredictionModel, PredictionModelRunTimestamp.prediction_model_id == PredictionModel.id
        )
        .where(PredictionModelRunTimestamp.interpolated == True)
        .where(PredictionModel.abbreviation == model.value)
        .order_by(PredictionModelRunTimestamp.prediction_run_timestamp.desc())
        .limit(1)
    )
    result = await session.scalar(stmt)

    return result
