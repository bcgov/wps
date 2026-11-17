"""CRUD operations for management of weather model data."""

import datetime
import logging
from typing import List

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from wps_shared.db.models.weather_models import (
    ModelRunForSFMS,
    ModelRunPrediction,
    PredictionModel,
    PredictionModelRunTimestamp,
    ProcessedModelRunUrl,
    SavedModelRunForSFMSUrl,
    WeatherStationModelPrediction,
)
from wps_shared.schemas.weather_models import ModelPredictionDetails
from wps_shared.utils.time import get_utc_now
from wps_shared.weather_models import ModelEnum, ProjectionEnum

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
            PredictionModelRunTimestamp.prediction_run_timestamp,
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


async def get_latest_daily_model_prediction_for_stations(
    session: Session,
    station_codes: list[int],
    prediction_run_timestamp_id: int,
) -> list[ModelPredictionDetails]:
    """
    Retrieves the most recent model predictions for each station and day, ensuring that only
    predictions with a timestamp at 20:00 hours are included.

    :param session: SQLAlchemy session used to execute the query.
    :param station_codes: List of station codes to filter the predictions.
    :param prediction_run_timestamp_id: ID of the prediction model run timestamp to filter predictions.
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
            WeatherStationModelPrediction.prediction_model_run_timestamp_id
            == prediction_run_timestamp_id,
            PredictionModelRunTimestamp.interpolated == True,
        )
        .order_by(
            WeatherStationModelPrediction.station_code,
            WeatherStationModelPrediction.prediction_timestamp.asc(),
        )
    )
    results = await session.execute(stmt)
    latest_predictions = [ModelPredictionDetails(**row) for row in results.mappings().all()]

    return latest_predictions


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


async def get_model_and_run_timestamp(
    session: AsyncSession, prediction_run_timestamp_id: int
) -> tuple[ModelEnum, datetime.datetime] | None:
    """Get the model and run time of a prediction model run, or None if there is no such run."""
    stmt = (
        select(PredictionModel.abbreviation, PredictionModelRunTimestamp.prediction_run_timestamp)
        .join(
            PredictionModel, PredictionModel.id == PredictionModelRunTimestamp.prediction_model_id
        )
        .where(PredictionModelRunTimestamp.id == prediction_run_timestamp_id)
    )
    row = (await session.execute(stmt)).one_or_none()
    if row is None:
        return None
    return ModelEnum(row.abbreviation), row.prediction_run_timestamp


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
        # prefer the finer ECMWF grid when both resolutions have the same run time
        .order_by((PredictionModel.projection == ProjectionEnum.ECMWF_LATLON_0_1.value).desc())
        .limit(1)
    )
    result = await session.scalar(stmt)

    return result


# The columns of weather_station_model_predictions that are stored in the `runs` table in object storage.
_STATION_RUN_COLUMNS = (
    "station_code",
    "prediction_timestamp",
    "tmp_tgl_2",
    "rh_tgl_2",
    "apcp_sfc_0",
    "wdir_tgl_10",
    "wind_tgl_10",
    "bias_adjusted_temperature",
    "bias_adjusted_rh",
    "bias_adjusted_wdir",
    "bias_adjusted_wind_speed",
    "delta_precip",
    "precip_24h",
    "bias_adjusted_precip_24h",
)


def get_station_run_rows(session: Session, model_run_id: int) -> list[dict]:
    """Get a model run's station predictions as rows for the `runs` table in object storage.

    A row is interpolated if the model itself has no prediction at that time. That can only be
    told while the run's model_run_predictions still exist, so `is_interpolated` is None once
    the retention policy has deleted them.
    """
    model_times = set(
        session.execute(
            select(ModelRunPrediction.prediction_timestamp)
            .where(ModelRunPrediction.prediction_model_run_timestamp_id == model_run_id)
            .distinct()
        ).scalars()
    )
    result = session.execute(
        select(
            *[getattr(WeatherStationModelPrediction, column) for column in _STATION_RUN_COLUMNS]
        ).where(WeatherStationModelPrediction.prediction_model_run_timestamp_id == model_run_id)
    )
    rows = []
    for mapping in result.mappings():
        row = dict(mapping)
        row["is_interpolated"] = (
            row["prediction_timestamp"] not in model_times if model_times else None
        )
        rows.append(row)
    return rows
