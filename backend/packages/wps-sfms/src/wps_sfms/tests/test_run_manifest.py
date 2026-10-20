"""Unit tests for SFMS run manifests."""

import json
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import (
    FBPParameter,
    FWIParameter,
    SFMSInterpolatedWeatherParameter,
)

from wps_sfms.raster_inputs import FoliarMoistureContentInputs
from wps_sfms.run_manifest import MANIFEST_SCHEMA_VERSION, SFMSRunManifest
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

RUN_DATETIME = datetime(2026, 10, 13, 20, 45, tzinfo=timezone.utc)
FOR_DATE = date(2026, 10, 13)


@pytest.fixture
def bucket(monkeypatch):
    """Point the object store at a known bucket, so GDAL prefixes can be stripped."""
    monkeypatch.setenv("OBJECT_STORE_BUCKET", "some bucket")


def a_manifest() -> SFMSRunManifest:
    """An actual-run manifest for one target date."""
    return SFMSRunManifest(SFMSNGRasterAddresser(), run_type=RunType.ACTUAL, for_date=FOR_DATE, run_datetime=RUN_DATETIME)


def record_everything(manifest: SFMSRunManifest) -> None:
    """Record every section the pipeline fills in for one actual run."""
    manifest.record_station_codes([122, 346])
    manifest.record_base_fuel_raster("sfms/static/fuel/2026/fbp2026_v1.tif")
    manifest.record_percent_conifer_raster("/vsis3/some bucket/sfms/static/m12_2026.tif")
    manifest.record_julian_rasters(
        {
            "green_up_on": "sfms_ng/static/julian/archive/green_up_on/on-hash.tif",
            "green_up_off": "sfms_ng/static/julian/archive/green_up_off/off-hash.tif",
            "grass_standing": "sfms_ng/static/julian/archive/grass_standing/standing-hash.tif",
            "grass_matted": "sfms_ng/static/julian/archive/grass_matted/matted-hash.tif",
        }
    )
    manifest.record_temporal_fuel_raster(
        "/vsis3/some bucket/sfms_ng/fuel/temporal/2026/10/13/2/fbp2026_10_13_2.tif"
    )
    manifest.record_seed_rasters(
        {
            FWIParameter.FFMC: "sfms_ng/actual/2026/10/12/ffmc_20261012.tif",
            FWIParameter.DMC: "sfms_ng/actual/2026/10/12/dmc_20261012.tif",
            FWIParameter.DC: "sfms_ng/actual/2026/10/12/dc_20261012.tif",
        }
    )
    manifest.record_static_rasters(
        {
            "dem": "/vsis3/some bucket/sfms/static/bc_elevation.tif",
            "mask": "/vsis3/some bucket/sfms/static/bc_mask.tif",
            "slope": "sfms_ng/static/bc_slope.tif",
            "aspect": "sfms_ng/static/bc_aspect.tif",
        }
    )
    fmc_inputs = FoliarMoistureContentInputs(
        fuel_key="/vcis3/some bucket/sfms/static/fuel/2026/fbp2026_v1.tif",
        elevation_key="/vsis3/some bucket/sfms_ng/static/bc_elevation.tif",
        latitude_key="/vsis3/some bucket/sfms_ng/static/latitude.tif",
        longitude_key="/vsis3/some bucket/sfms_ng/static/longitude.tif",
        output_keys={FOR_DATE: "sfms_ng/static/fmc/2026/10/13/fmc_20261013.tif"},
    )
    manifest.record_fmc_static_inputs(fmc_inputs)
    # an earlier run calculated the date's FMC, so this one reuses it
    manifest.record_reused_fmc_raster(fmc_inputs.output_keys[FOR_DATE])
    for weather_param in SFMSInterpolatedWeatherParameter:
        manifest.record_raster_output(
            weather_param, f"sfms_ng/actual/2026/10/13/{weather_param.value}_20261013.tif"
        )
    for fwi_param in FWIParameter:
        manifest.record_raster_output(
            fwi_param, f"sfms_ng/actual/2026/10/13/{fwi_param.value}_20261013.tif"
        )
    for fbp_param in FBPParameter:
        manifest.record_raster_output(
            fbp_param, f"sfms_ng/actual/2026/10/13/{fbp_param.value}_20261013.tif"
        )


def test_records_keys_with_the_gdal_prefix_stripped(bucket):
    manifest = a_manifest()

    manifest.record_static_rasters(
        {
            "mask": "/vsis3/some bucket/sfms/static/bc_mask.tif",
            "slope": "sfms_ng/static/bc_slope.tif",
        }
    )

    # a GDAL path is stripped to its key, and a plain key passes through
    assert manifest.input.static_rasters == {
        "mask": "sfms/static/bc_mask.tif",
        "slope": "sfms_ng/static/bc_slope.tif",
    }


def test_key_uses_the_run_type_and_target_date_folder():
    manifest = a_manifest()

    assert manifest.key() == (
        "sfms_ng/runs/actual/2026/10/13/target-2026-10-13_run-2026-10-13T20-45-00.000000Z.json"
    )


def test_forecast_key_uses_the_forecast_date_folder():
    manifest = SFMSRunManifest(
        SFMSNGRasterAddresser(),
        run_type=RunType.FORECAST,
        for_date=date(2026, 10, 14),
        run_datetime=RUN_DATETIME,
    )

    # forecast runs process dates after the run datetime; the folder is the forecast date
    assert manifest.key() == (
        "sfms_ng/runs/forecast/2026/10/14/target-2026-10-14_run-2026-10-13T20-45-00.000000Z.json"
    )


def test_key_rejects_non_utc_run_datetime():
    manifest = SFMSRunManifest(
        SFMSNGRasterAddresser(),
        run_type=RunType.ACTUAL,
        for_date=FOR_DATE,
        run_datetime=datetime(2026, 10, 13, 20, 45, tzinfo=timezone(timedelta(hours=-7))),
    )

    with pytest.raises(AssertionError, match="is not in UTC"):
        manifest.key()


def test_manifest_json_follows_the_version_1_schema(bucket):
    manifest = a_manifest()
    record_everything(manifest)
    manifest.status = "success"

    payload = json.loads(manifest.model_dump_json(indent=2, exclude_none=True))

    assert payload == {
        "version": MANIFEST_SCHEMA_VERSION,
        "run_datetime": "2026-10-13T20:45:00Z",
        "run_type": "actual",
        "for_date": "2026-10-13",
        "status": "success",
        "input": {
            "station_codes": [122, 346],
            "fuel_raster": {
                "base": "sfms/static/fuel/2026/fbp2026_v1.tif",
                "temporal": "sfms_ng/fuel/temporal/2026/10/13/2/fbp2026_10_13_2.tif",
                "percent_conifer": "sfms/static/m12_2026.tif",
            },
            "seed_rasters": {
                "ffmc": "sfms_ng/actual/2026/10/12/ffmc_20261012.tif",
                "dmc": "sfms_ng/actual/2026/10/12/dmc_20261012.tif",
                "dc": "sfms_ng/actual/2026/10/12/dc_20261012.tif",
            },
            "static_rasters": {
                "dem": "sfms/static/bc_elevation.tif",
                "mask": "sfms/static/bc_mask.tif",
                "slope": "sfms_ng/static/bc_slope.tif",
                "aspect": "sfms_ng/static/bc_aspect.tif",
                "elevation": "sfms_ng/static/bc_elevation.tif",
                "latitude": "sfms_ng/static/latitude.tif",
                "longitude": "sfms_ng/static/longitude.tif",
            },
            "julian_rasters": {
                "green_up_on": "sfms_ng/static/julian/archive/green_up_on/on-hash.tif",
                "green_up_off": "sfms_ng/static/julian/archive/green_up_off/off-hash.tif",
                "grass_standing": "sfms_ng/static/julian/archive/grass_standing/standing-hash.tif",
                "grass_matted": "sfms_ng/static/julian/archive/grass_matted/matted-hash.tif",
            },
            "fmc_raster": "sfms_ng/static/fmc/2026/10/13/fmc_20261013.tif",
        },
        "output": {
            "weather": {
                param.value: f"sfms_ng/actual/2026/10/13/{param.value}_20261013.tif"
                for param in SFMSInterpolatedWeatherParameter
            },
            "fwi": {
                param.value: f"sfms_ng/actual/2026/10/13/{param.value}_20261013.tif"
                for param in FWIParameter
            },
            "fbp": {
                param.value: f"sfms_ng/actual/2026/10/13/{param.value}_20261013.tif"
                for param in FBPParameter
            },
            "fuel_raster": "sfms_ng/fuel/temporal/2026/10/13/2/fbp2026_10_13_2.tif",
        },
        "reused": {
            "fmc_raster": "sfms_ng/static/fmc/2026/10/13/fmc_20261013.tif",
        },
    }


def test_manifest_records_only_the_steps_that_ran(bucket):
    manifest = a_manifest()
    manifest.record_station_codes([122])
    for weather_param in SFMSInterpolatedWeatherParameter:
        manifest.record_raster_output(
            weather_param, f"sfms_ng/actual/2026/10/13/{weather_param.value}_20261013.tif"
        )

    assert manifest.output.weather == {
        param.value: f"sfms_ng/actual/2026/10/13/{param.value}_20261013.tif"
        for param in SFMSInterpolatedWeatherParameter
    }
    assert manifest.output.fwi == {}
    assert manifest.output.fbp == {}
    assert manifest.output.fuel_raster is None
    assert manifest.input.fuel_raster.base is None
    assert manifest.input.seed_rasters == {}
    payload = json.loads(manifest.model_dump_json(indent=2, exclude_none=True))
    assert payload["input"]["fuel_raster"] == {}
    assert payload["reused"] == {}


def test_manifest_records_failure_and_preserves_partial_trace():
    manifest = a_manifest()
    manifest.record_station_codes([122])
    manifest.record_raster_output(
        SFMSInterpolatedWeatherParameter.TEMP,
        "sfms_ng/actual/2026/10/13/temperature_20261013.tif",
    )

    manifest.record_failure("relative_humidity_interpolation", RuntimeError("RH failed"))
    manifest.record_failure("later_step", ValueError("later failure"))

    assert manifest.status == "failed"
    assert manifest.failed_step == "relative_humidity_interpolation"
    assert manifest.failure_type == "RuntimeError"
    assert manifest.failure_message == "RH failed"
    assert manifest.output.weather == {
        "temperature": "sfms_ng/actual/2026/10/13/temperature_20261013.tif"
    }
    payload = json.loads(manifest.model_dump_json(indent=2, exclude_none=True))
    assert payload["status"] == "failed"
    assert payload["failed_step"] == "relative_humidity_interpolation"


def test_record_raster_output_rejects_an_unsupported_parameter():
    manifest = a_manifest()

    with pytest.raises(ValueError, match="Unsupported raster output parameter"):
        manifest.record_raster_output("not a parameter", "sfms_ng/actual/2026/10/13/x.tif")


@pytest.mark.anyio
async def test_write_uploads_the_manifest_json(bucket):
    manifest = a_manifest()
    manifest.record_station_codes([122])
    s3_client = MagicMock()
    s3_client.put_object = AsyncMock()

    await manifest.write(s3_client)

    key = s3_client.put_object.await_args.kwargs["key"]
    body = s3_client.put_object.await_args.kwargs["body"]
    assert key == ("sfms_ng/runs/actual/2026/10/13/target-2026-10-13_run-2026-10-13T20-45-00.000000Z.json")
    payload = json.loads(body)
    assert payload["version"] == MANIFEST_SCHEMA_VERSION
    assert payload["status"] == "success"
    assert payload["run_datetime"] == "2026-10-13T20:45:00Z"
    assert payload["run_type"] == "actual"
    assert payload["for_date"] == "2026-10-13"
    assert payload["input"]["station_codes"] == [122]
