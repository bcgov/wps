"""Shared mocks for the SFMS daily actuals and forecast job tests."""

from contextlib import asynccontextmanager
from datetime import date
from typing import NamedTuple
from unittest.mock import AsyncMock, MagicMock

from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from wps_sfms.processors.foliar_moisture_content import (
    FoliarMoistureContentKeys,
    FoliarMoistureContentProcessor,
)
from wps_sfms.processors.fwi import FWIProcessor
from wps_sfms.processors.idw import Interpolator
from wps_sfms.processors.primary_fire_behaviour import PrimaryFireBehaviourProcessor
from wps_sfms.processors.relative_humidity import RHInterpolator
from wps_sfms.processors.temperature import TemperatureInterpolator
from wps_sfms.processors.wind import WindDirectionInterpolator, WindSpeedInterpolator
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.sfms.raster_addresser import FBPParameter

from app.tests.conftest import create_mock_sfms_actuals


def raster_key(datetime_utc, parameter, run_type):
    """A realistic raster key for a weather, FWI, or FBP parameter."""
    return (
        f"sfms_ng/{run_type.value}/{datetime_utc:%Y/%m/%d}/"
        f"{parameter.value}_{datetime_utc:%Y%m%d}.tif"
    )


def fmc_key(target_date: date) -> str:
    """A realistic FMC output key for a target date."""
    return f"sfms_ng/static/fmc/{target_date:%Y/%m/%d}/fmc_{target_date:%Y%m%d}.tif"


class MockDailySFMSDeps(NamedTuple):
    """Mock dependencies shared by the SFMS daily actuals and forecast tests."""

    db_session: MagicMock
    s3_client: MagicMock
    temp_processor: MagicMock
    rh_processor: MagicMock
    wind_speed_processor: MagicMock
    wind_direction_processor: MagicMock
    interpolation_processor: MagicMock
    danger_rating_processor: MagicMock
    fwi_processor: MagicMock
    primary_fbp_processor: MagicMock
    find_temporal_fuel: AsyncMock
    fmc_processor: MagicMock
    fmc_processor_class: MagicMock
    fmc_inputs: MagicMock
    wfwx_api: MagicMock
    addresser: MagicMock
    save_sfms_run: AsyncMock
    get_fuel_type_raster_by_year: AsyncMock


def make_mock_daily_sfms_dependencies(
    mocker: MockerFixture,
    monkeypatch,
    module_path: str,
    mock_s3_client,
    mock_wfwx_api,
) -> MockDailySFMSDeps:
    """Build the shared external dependency mocks for a daily SFMS job module."""
    monkeypatch.setenv("OBJECT_STORE_BUCKET", "test-bucket")
    mocker.patch(f"{module_path}.S3Client", return_value=mock_s3_client)
    mock_s3_client.all_objects_exist = AsyncMock(return_value=True)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mocker.patch(f"{module_path}.ClientSession", return_value=mock_session)

    station_dailies = create_mock_sfms_actuals()
    station_dailies[0].danger_rating = 4
    mock_wfwx_api.get_sfms_daily_weather_all_stations = AsyncMock(return_value=station_dailies)
    mocker.patch(f"{module_path}.WfwxApi", return_value=mock_wfwx_api)

    fuel_type_raster = MagicMock(year=2024, object_store_path="sfms/fuel/2024/fuel.tif")
    get_fuel_type_raster_by_year = mocker.patch(
        f"{module_path}.get_fuel_type_raster_by_year",
        new_callable=AsyncMock,
        return_value=fuel_type_raster,
    )

    read_session = MagicMock(spec=AsyncSession)

    @asynccontextmanager
    async def _read_scope():
        yield read_session

    mocker.patch(f"{module_path}.get_async_read_session_scope", _read_scope)

    save_sfms_run = mocker.patch(
        f"{module_path}.save_sfms_run", new_callable=AsyncMock, return_value=1
    )

    addresser = MagicMock()
    addresser.s3_prefix = "/vsis3/test-bucket"
    mocker.patch(f"{module_path}.SFMSNGRasterAddresser", return_value=addresser)
    addresser.get_percent_conifer_key.side_effect = lambda year: f"sfms/static/m12_{year}.tif"
    addresser.get_slope_key.side_effect = lambda: "sfms_ng/static/bc_slope.tif"
    addresser.get_aspect_key.side_effect = lambda: "sfms_ng/static/bc_aspect.tif"
    addresser.get_dem_key.side_effect = lambda: "/vsis3/test-bucket/sfms/static/bc_elevation.tif"
    addresser.get_mask_key.side_effect = lambda: "/vsis3/test-bucket/sfms/static/bc_mask.tif"
    addresser.get_weather_key.side_effect = raster_key
    addresser.get_index_key.side_effect = raster_key
    addresser.get_fbp_key.side_effect = raster_key
    addresser.get_danger_rating_key.side_effect = lambda datetime_utc, run_type: (
        f"sfms_ng/{run_type.value}/{datetime_utc:%Y/%m/%d}/danger_rating_{datetime_utc:%Y%m%d}.tif"
    )
    # the real FWI input builder, over the mocked key helpers
    addresser.get_fwi_inputs.side_effect = lambda *args: SFMSNGRasterAddresser.get_fwi_inputs(
        addresser, *args
    )
    addresser.get_primary_fire_behaviour_inputs.side_effect = (
        lambda datetime_to_process, run_type, *_args: MagicMock(
            output_keys={
                parameter: raster_key(datetime_to_process, parameter, run_type)
                for parameter in FBPParameter
            },
        )
    )
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/test-bucket/{key}"
    # the manifest names its key and strips GDAL prefixes with the run's addresser
    real_addresser = SFMSNGRasterAddresser()
    addresser.s3_key.side_effect = real_addresser.s3_key
    addresser.get_run_manifest_key.side_effect = real_addresser.get_run_manifest_key

    fmc_inputs = MagicMock()
    fmc_inputs.output_keys.__getitem__.side_effect = fmc_key
    fmc_inputs.elevation_key = "/vsis3/test-bucket/sfms_ng/static/bc_elevation.tif"
    fmc_inputs.latitude_key = "/vsis3/test-bucket/sfms_ng/static/latitude.tif"
    fmc_inputs.longitude_key = "/vsis3/test-bucket/sfms_ng/static/longitude.tif"
    addresser.get_fmc_inputs.return_value = fmc_inputs
    fmc_processor = MagicMock(spec=FoliarMoistureContentProcessor)
    # every date's FMC raster is processed rather than reused
    processed_fmc_keys = MagicMock()
    processed_fmc_keys.__getitem__.side_effect = fmc_key
    fmc_processor.process = AsyncMock(
        return_value=FoliarMoistureContentKeys(processed_keys=processed_fmc_keys, reused_keys={})
    )
    fmc_processor_class = mocker.patch(
        "wps_sfms.fmc_step.FoliarMoistureContentProcessor", return_value=fmc_processor
    )

    temp_processor = MagicMock(spec=TemperatureInterpolator)
    temp_processor.process = AsyncMock(return_value="temperature.tif")
    mocker.patch("wps_sfms.weather_step.TemperatureInterpolator", return_value=temp_processor)

    rh_processor = MagicMock(spec=RHInterpolator)
    rh_processor.process = AsyncMock(return_value="relative_humidity.tif")
    mocker.patch("wps_sfms.weather_step.RHInterpolator", return_value=rh_processor)

    wind_speed_processor = MagicMock(spec=WindSpeedInterpolator)
    wind_speed_processor.process = AsyncMock(return_value="wind_speed.tif")
    mocker.patch("wps_sfms.weather_step.WindSpeedInterpolator", return_value=wind_speed_processor)

    wind_direction_processor = MagicMock(spec=WindDirectionInterpolator)
    wind_direction_processor.process = AsyncMock(return_value="wind_direction.tif")
    mocker.patch(
        "wps_sfms.weather_step.WindDirectionInterpolator", return_value=wind_direction_processor
    )

    interpolation_processor = MagicMock(spec=Interpolator)
    interpolation_processor.process = AsyncMock(return_value="precipitation.tif")
    # the weather step interpolates precipitation, the FWI step Monday FFMC, DMC and DC
    mocker.patch("wps_sfms.weather_step.Interpolator", return_value=interpolation_processor)
    mocker.patch("wps_sfms.fwi_step.Interpolator", return_value=interpolation_processor)

    danger_rating_processor = MagicMock(spec=Interpolator)
    danger_rating_processor.process = AsyncMock(return_value="danger_rating.tif")
    mocker.patch(
        "wps_sfms.danger_rating_step.Interpolator",
        return_value=danger_rating_processor,
    )

    fwi_processor = MagicMock(spec=FWIProcessor)
    fwi_processor.calculate_index = AsyncMock(return_value=None)
    mocker.patch("wps_sfms.fwi_step.FWIProcessor", return_value=fwi_processor)

    primary_fbp_processor = MagicMock(spec=PrimaryFireBehaviourProcessor)
    primary_fbp_processor.process = AsyncMock(return_value=None)
    mocker.patch(
        "wps_sfms.fbp_step.PrimaryFireBehaviourProcessor", return_value=primary_fbp_processor
    )

    db_session = MagicMock(spec=AsyncSession)
    execute_result = MagicMock()
    execute_result.scalar = MagicMock(return_value=1)
    db_session.execute = AsyncMock(return_value=execute_result)
    db_session.get = AsyncMock(return_value=MagicMock())
    db_session.commit = AsyncMock()

    @asynccontextmanager
    async def _write_scope():
        yield db_session
        await db_session.commit()

    # the job saves its run, and each tracked job commits its own run log rows
    mocker.patch(f"{module_path}.get_async_write_session_scope", _write_scope)
    mocker.patch("wps_sfms.temporal_fuel_step.get_async_write_session_scope", _write_scope)
    mocker.patch("wps_shared.db.crud.sfms_run.get_async_write_session_scope", _write_scope)

    # the temporal fuel step reuses an existing grid for each date, at a fixed path
    julian = MagicMock()
    julian.__iter__.side_effect = lambda: iter(())
    julian.hash_columns.return_value = {}
    mocker.patch(
        "wps_sfms.temporal_fuel_step.read_julian_rasters",
        new_callable=AsyncMock,
        return_value=julian,
    )
    mocker.patch("wps_sfms.temporal_fuel_step.ensure_julian_archives", new_callable=AsyncMock)
    mocker.patch(
        "wps_sfms.temporal_fuel_step.lock_temporal_fuel_raster_date", new_callable=AsyncMock
    )
    mocker.patch(
        "wps_sfms.temporal_fuel_step._stored_raster_matches",
        new_callable=AsyncMock,
        return_value=True,
    )
    find_temporal_fuel = mocker.patch(
        "wps_sfms.temporal_fuel_step.get_matching_temporal_fuel_raster",
        new_callable=AsyncMock,
        side_effect=lambda _session, target_date, *_args, **_hashes: MagicMock(
            object_store_path=f"temporal/{target_date}.tif"
        ),
    )

    return MockDailySFMSDeps(
        db_session=db_session,
        s3_client=mock_s3_client,
        temp_processor=temp_processor,
        rh_processor=rh_processor,
        wind_speed_processor=wind_speed_processor,
        wind_direction_processor=wind_direction_processor,
        interpolation_processor=interpolation_processor,
        danger_rating_processor=danger_rating_processor,
        fwi_processor=fwi_processor,
        primary_fbp_processor=primary_fbp_processor,
        find_temporal_fuel=find_temporal_fuel,
        fmc_processor=fmc_processor,
        fmc_processor_class=fmc_processor_class,
        fmc_inputs=fmc_inputs,
        wfwx_api=mock_wfwx_api,
        addresser=addresser,
        save_sfms_run=save_sfms_run,
        get_fuel_type_raster_by_year=get_fuel_type_raster_by_year,
    )
