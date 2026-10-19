"""Shared helpers for testing the stages of an SFMS run."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.run_type import RunType
from wps_shared.schemas.sfms import SFMSDaily
from wps_shared.sfms.raster_addresser import FWIParameter, SFMSInterpolatedWeatherParameter

from wps_sfms.run_context import SFMSRunContext

RUN_DATETIME = datetime(2025, 7, 4, 20, 45, tzinfo=timezone.utc)

# the raster keys the stages under test are handed by the stages that wrote them, for 2025-07-04
WEATHER_KEYS = {
    param: f"sfms_ng/actual/2025/07/04/{param.value}_20250704.tif"
    for param in SFMSInterpolatedWeatherParameter
}

FWI_KEYS = {
    param: f"sfms_ng/actual/2025/07/04/{param.value}_20250704.tif" for param in FWIParameter
}

FMC_KEY = "sfms_ng/static/fmc/2025/07/04/fmc_20250704.tif"


def datetime_to_process_for(for_date: date) -> datetime:
    """The hour-20 UTC datetime a target date is processed at."""
    return datetime(for_date.year, for_date.month, for_date.day, 20, tzinfo=timezone.utc)


def a_run(
    for_date: date = date(2025, 7, 4),
    run_type: RunType = RunType.ACTUAL,
    sfms_run_id: int = 42,
    addresser: MagicMock | None = None,
    s3_client: MagicMock | None = None,
    fuel_type_raster: MagicMock | None = None,
    seed_actual_date: date | None = None,
) -> SFMSRunContext:
    """A run context for one target date, tracing into a real manifest.

    It seeds from the previous day's actuals unless given another ``seed_actual_date``.
    """
    return SFMSRunContext.start(
        datetime_to_process_for(for_date),
        run_type,
        sfms_run_id,
        RUN_DATETIME,
        s3_client or MagicMock(),
        addresser or MagicMock(),
        fuel_type_raster=fuel_type_raster
        or MagicMock(year=for_date.year, object_store_path="sfms/fuel/fuel.tif"),
        seed_actual_date=seed_actual_date or for_date - timedelta(days=1),
        station_codes=(),
    )


def station_weather() -> list[SFMSDaily]:
    """Two stations' daily weather, enough to build every interpolation field."""
    for_datetime = datetime(2025, 7, 4, 20, tzinfo=timezone.utc)
    return [
        SFMSDaily(
            code=100,
            for_datetime=for_datetime,
            run_type=RunTypeEnum.actual,
            lat=49.0,
            lon=-123.0,
            elevation=100.0,
            temperature=15.0,
            relative_humidity=50.0,
            precipitation=2.5,
            wind_speed=10.0,
            wind_direction=180.0,
            ffmc=85.0,
            dmc=30.0,
            dc=200.0,
        ),
        SFMSDaily(
            code=101,
            for_datetime=for_datetime,
            run_type=RunTypeEnum.actual,
            lat=49.5,
            lon=-123.5,
            elevation=200.0,
            temperature=12.0,
            relative_humidity=60.0,
            precipitation=5.0,
            wind_speed=8.0,
            wind_direction=200.0,
            ffmc=80.0,
            dmc=25.0,
            dc=180.0,
        ),
    ]


@pytest.fixture
def some_bucket(monkeypatch):
    """Point the object store at the bucket the stage tests' GDAL paths use."""
    monkeypatch.setenv("OBJECT_STORE_BUCKET", "some bucket")


@pytest.fixture
def tracked_jobs(mocker: MockerFixture) -> list[SFMSRunLogJobName]:
    """Run SFMS tracked jobs without the run log, collecting the job names they ran under."""
    job_names = []

    def track_sfms_run(job_name, _sfms_run_id):
        def decorator(fn):
            async def wrapper(*args, **kwargs):
                job_names.append(job_name)
                return await fn(*args, **kwargs)

            return wrapper

        return decorator

    mocker.patch("wps_sfms.run_context.track_sfms_run", side_effect=track_sfms_run)
    return job_names
