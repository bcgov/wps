"""Tests for the SFMS FWI steps."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import (
    FWIParameter,
)

from wps_sfms.fwi_step import calculate_fwi, interpolate_fwi, missing_seed_keys
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_sfms.tests.run_test_utils import (
    WEATHER_KEYS,
    a_run,
    station_weather,
)

# manifest keys strip this bucket's GDAL prefix
pytestmark = pytest.mark.usefixtures("some_bucket")


def stub_fwi_addresser(addresser: MagicMock) -> None:
    """Give an addresser realistic index and FWI input keys for the given run."""

    def index_key(datetime_utc, fwi_param, run_type):
        return (
            f"sfms_ng/{run_type.value}/{datetime_utc:%Y/%m/%d}/"
            f"{fwi_param.value}_{datetime_utc:%Y%m%d}.tif"
        )

    addresser.get_index_key.side_effect = index_key
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/some bucket/{key}"
    # the real FWI input builder, over the stubbed key helpers
    addresser.get_fwi_inputs.side_effect = lambda *args: SFMSNGRasterAddresser.get_fwi_inputs(
        addresser, *args
    )


@pytest.mark.anyio
async def test_fwi_calculation_step_records_seed_rasters_and_outputs(
    mocker: MockerFixture, tracked_jobs
):
    addresser = MagicMock()
    stub_fwi_addresser(addresser)
    s3_client = MagicMock()
    s3_client.all_objects_exist = AsyncMock(return_value=True)
    fwi_processor = MagicMock()
    fwi_processor.calculate_index = AsyncMock()
    mocker.patch("wps_sfms.fwi_step.FWIProcessor", return_value=fwi_processor)
    run = a_run(addresser=addresser, s3_client=s3_client)

    fwi_keys = await calculate_fwi(run, WEATHER_KEYS)

    manifest = run.manifest
    assert fwi_keys == {
        param: f"sfms_ng/actual/2025/07/04/{param.value}_20250704.tif" for param in FWIParameter
    }
    # ISI reads the same-day FFMC the step just calculated, not a seed
    isi_inputs = fwi_processor.calculate_index.await_args_list[3].args[3]
    assert isi_inputs.index_keys == {
        FWIParameter.FFMC: "/vsis3/some bucket/sfms_ng/actual/2025/07/04/ffmc_20250704.tif"
    }
    assert manifest.input.seed_rasters == {
        "ffmc": "sfms_ng/actual/2025/07/03/ffmc_20250703.tif",
        "dmc": "sfms_ng/actual/2025/07/03/dmc_20250703.tif",
        "dc": "sfms_ng/actual/2025/07/03/dc_20250703.tif",
    }
    assert manifest.output.fwi == {
        "ffmc": "sfms_ng/actual/2025/07/04/ffmc_20250704.tif",
        "dmc": "sfms_ng/actual/2025/07/04/dmc_20250704.tif",
        "dc": "sfms_ng/actual/2025/07/04/dc_20250704.tif",
        "isi": "sfms_ng/actual/2025/07/04/isi_20250704.tif",
        "bui": "sfms_ng/actual/2025/07/04/bui_20250704.tif",
        "fwi": "sfms_ng/actual/2025/07/04/fwi_20250704.tif",
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("seed_actual_date", "seed_run_type"),
    [(date(2025, 7, 3), "actual"), (date(2025, 7, 2), "forecast")],
    ids=["day after the latest actual", "later forecast day"],
)
async def test_forecast_seeds_from_the_latest_actual_then_from_forecasts(
    mocker: MockerFixture, tracked_jobs, seed_actual_date: date, seed_run_type: str
):
    addresser = MagicMock()
    stub_fwi_addresser(addresser)
    s3_client = MagicMock()
    s3_client.all_objects_exist = AsyncMock(return_value=True)
    fwi_processor = MagicMock()
    fwi_processor.calculate_index = AsyncMock()
    mocker.patch("wps_sfms.fwi_step.FWIProcessor", return_value=fwi_processor)
    run = a_run(
        run_type=RunType.FORECAST,
        addresser=addresser,
        s3_client=s3_client,
        seed_actual_date=seed_actual_date,
    )

    await calculate_fwi(run, WEATHER_KEYS)

    assert run.manifest.input.seed_rasters == {
        param: f"sfms_ng/{seed_run_type}/2025/07/03/{param}_20250703.tif"
        for param in ("ffmc", "dmc", "dc")
    }


@pytest.mark.anyio
async def test_fwi_calculation_step_skips_fwi_when_seeds_are_missing(mocker: MockerFixture):
    addresser = MagicMock()
    stub_fwi_addresser(addresser)
    s3_client = MagicMock()
    s3_client.all_objects_exist = AsyncMock(return_value=False)
    fwi_processor = MagicMock()
    fwi_processor.calculate_index = AsyncMock()
    mocker.patch("wps_sfms.fwi_step.FWIProcessor", return_value=fwi_processor)
    run = a_run(addresser=addresser, s3_client=s3_client)

    fwi_keys = await calculate_fwi(run, WEATHER_KEYS)

    assert fwi_keys is None
    fwi_processor.calculate_index.assert_not_awaited()
    assert run.manifest.input.seed_rasters == {}
    assert run.manifest.output.fwi == {}


@pytest.mark.anyio
async def test_fwi_interpolation_step_derives_isi_bui_and_fwi_from_the_interpolated_codes(
    mocker: MockerFixture, tracked_jobs
):
    addresser = MagicMock()
    stub_fwi_addresser(addresser)
    addresser.get_mask_key.return_value = "/vsis3/some bucket/sfms/static/bc_mask.tif"
    interpolator = mocker.patch("wps_sfms.fwi_step.Interpolator").return_value
    interpolator.process = AsyncMock()
    fwi_processor = MagicMock()
    fwi_processor.calculate_index = AsyncMock()
    mocker.patch("wps_sfms.fwi_step.FWIProcessor", return_value=fwi_processor)
    run = a_run(addresser=addresser)

    fwi_keys = await interpolate_fwi(run, station_weather(), WEATHER_KEYS)

    def today(param: FWIParameter) -> str:
        return f"sfms_ng/actual/2025/07/04/{param.value}_20250704.tif"

    assert fwi_keys == {param: today(param) for param in FWIParameter}
    # FFMC, DMC and DC are reset from station weather, then ISI, BUI and FWI derive from them
    assert tracked_jobs == [
        SFMSRunLogJobName.FFMC_INTERPOLATION,
        SFMSRunLogJobName.DMC_INTERPOLATION,
        SFMSRunLogJobName.DC_INTERPOLATION,
        SFMSRunLogJobName.ISI_CALCULATION,
        SFMSRunLogJobName.BUI_CALCULATION,
        SFMSRunLogJobName.FWI_CALCULATION,
    ]
    isi_inputs, bui_inputs, fwi_inputs = (
        call.args[3] for call in fwi_processor.calculate_index.await_args_list
    )
    gdal = "/vsis3/some bucket/"
    assert isi_inputs.index_keys == {FWIParameter.FFMC: gdal + today(FWIParameter.FFMC)}
    assert bui_inputs.index_keys == {
        FWIParameter.DMC: gdal + today(FWIParameter.DMC),
        FWIParameter.DC: gdal + today(FWIParameter.DC),
    }
    assert fwi_inputs.index_keys == {
        FWIParameter.ISI: gdal + today(FWIParameter.ISI),
        FWIParameter.BUI: gdal + today(FWIParameter.BUI),
    }
    # no previous-day seeds are read when the codes are interpolated
    assert run.manifest.input.seed_rasters == {}
    assert run.manifest.input.static_rasters == {"mask": "sfms/static/bc_mask.tif"}
    assert run.manifest.output.fwi == {param.value: today(param) for param in FWIParameter}


@pytest.mark.anyio
@pytest.mark.parametrize("missing_param", [FWIParameter.FFMC, FWIParameter.DMC, FWIParameter.DC])
async def test_missing_seed_keys_returns_only_missing_keys(missing_param: FWIParameter):
    addresser = MagicMock()
    addresser.get_index_key.side_effect = lambda dt, param, run_type: (
        f"{run_type.value}_{param.value}_{dt:%Y%m%d}.tif"
    )
    missing_key = f"actual_{missing_param.value}_20240703.tif"
    s3_client = MagicMock()
    s3_client.all_objects_exist = AsyncMock(side_effect=lambda key: key != missing_key)
    datetime_to_process = datetime(2024, 7, 4, 20, tzinfo=timezone.utc)

    missing = await missing_seed_keys(datetime_to_process, addresser, s3_client, RunType.ACTUAL)

    assert missing == [f"{missing_param.value}={missing_key}"]
