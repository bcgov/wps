from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import cffdrs.fire_behaviour_prediction
import cffdrs.models
import cffdrs.surface_fuel_consumption
import numpy as np
import pytest
from pytest_mock import MockerFixture
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import FBPParameter

from wps_sfms.interpolation.common import SFMS_NO_DATA
from wps_sfms.processors.primary_fire_behaviour import (
    PrimaryFireBehaviourDatasets,
    PrimaryFireBehaviourProcessor,
    PrimaryFireBehaviourResult,
    calculate_primary_fire_behaviour,
)
from wps_sfms.raster_inputs import PrimaryFireBehaviourInputs
from wps_sfms.tests.raster_test_utils import TEST_INPUT_NODATA, create_test_wps_dataset

TEST_DATETIME = datetime(2024, 7, 4, 20, tzinfo=timezone.utc)


def make_datasets(fuel: np.ndarray, **overrides: np.ndarray) -> PrimaryFireBehaviourDatasets:
    shape = fuel.shape
    defaults = {
        "ffmc": np.full(shape, 90.0),
        "bui": np.full(shape, 60.0),
        "wind_speed": np.full(shape, 10.0),
        "wind_direction": np.full(shape, 0.0),
        "slope": np.full(shape, 5.0),
        "aspect": np.full(shape, 50.0),
        "percent_conifer": np.full(shape, 50.0),
        "fmc": np.full(shape, 100.0),
    }
    defaults.update(overrides)
    return PrimaryFireBehaviourDatasets(
        fuel=create_test_wps_dataset("fuel.tif", fuel.astype(np.float32)),
        **{
            name: create_test_wps_dataset(f"{name}.tif", array.astype(np.float32))
            for name, array in defaults.items()
        },
    )


def make_inputs() -> PrimaryFireBehaviourInputs:
    return PrimaryFireBehaviourInputs(
        fuel_key="/vsis3/test/fuel.tif",
        ffmc_key="/vsis3/test/ffmc.tif",
        bui_key="/vsis3/test/bui.tif",
        wind_speed_key="/vsis3/test/wind_speed.tif",
        wind_direction_key="/vsis3/test/wind_direction.tif",
        slope_key="/vsis3/test/slope.tif",
        aspect_key="/vsis3/test/aspect.tif",
        percent_conifer_key="/vsis3/test/percent_conifer.tif",
        fmc_key="/vsis3/test/fmc.tif",
        output_keys={
            FBPParameter.SFC: "sfms_ng/actual/2024/07/04/sfc_20240704.tif",
            FBPParameter.ROS: "sfms_ng/actual/2024/07/04/ros_20240704.tif",
            FBPParameter.HFI: "sfms_ng/actual/2024/07/04/hfi_20240704.tif",
            FBPParameter.TFC: "sfms_ng/actual/2024/07/04/tfc_20240704.tif",
            FBPParameter.CFB: "sfms_ng/actual/2024/07/04/cfb_20240704.tif",
        },
        run_type=RunType.ACTUAL,
    )


def make_dataset_context(datasets: PrimaryFireBehaviourDatasets, reverse: bool = False):
    @contextmanager
    def dataset_context(keys):
        input_datasets = [
            datasets.fuel,
            datasets.ffmc,
            datasets.bui,
            datasets.wind_speed,
            datasets.wind_direction,
            datasets.slope,
            datasets.aspect,
            datasets.percent_conifer,
            datasets.fmc,
        ]
        for dataset, key in zip(input_datasets, keys, strict=True):
            dataset.ds_path = key
        yield list(reversed(input_datasets)) if reverse else input_datasets

    return dataset_context


def test_calculation_matches_cffdrs_reference_and_derives_isi():
    """Regression test for radians, derived ISI, and the required int64 control arrays."""
    datasets = make_datasets(
        np.array([[6.0]]),
        wind_direction=np.array([[225.0]]),
    )

    result = calculate_primary_fire_behaviour(datasets)

    expected = cffdrs.fire_behaviour_prediction.fire_behaviour_prediction(
        cffdrs.models.FBPInput(
            fuel_type="C6",
            ffmc=90.0,
            bui=60.0,
            ws=10.0,
            wd=225.0,
            gs=5.0,
            aspect=50.0,
            pc=50.0,
            fmc=100.0,
            isi=0.0,
            lat=0.0,
            lon=0.0,
            elv=0.0,
        ),
        "Primary",
    )
    assert result.sfc[0, 0] == pytest.approx(expected.sfc, rel=1e-3)
    assert result.ros[0, 0] == pytest.approx(expected.ros, rel=1e-3)
    assert result.hfi[0, 0] == pytest.approx(expected.hfi, rel=1e-3)
    assert result.tfc[0, 0] == pytest.approx(expected.tfc, rel=1e-3)
    assert result.cfb[0, 0] == pytest.approx(expected.cfb, rel=1e-3)


def test_passes_zero_isi_to_primary_fbp(mocker: MockerFixture):
    primary_fbp = mocker.patch(
        "wps_sfms.processors.primary_fire_behaviour.vectorized_primary_fire_behaviour_prediction",
        return_value=SimpleNamespace(
            sfc=np.array([1.0]),
            ros=np.array([2.0]),
            hfi=np.array([3.0]),
            tfc=np.array([4.0]),
            cfb=np.array([0.5]),
        ),
    )

    calculate_primary_fire_behaviour(make_datasets(np.array([[6.0]])))

    np.testing.assert_array_equal(primary_fbp.call_args.args[14], np.array([0.0]))


@pytest.mark.parametrize(
    "grid_value,fuel_type,percent_conifer",
    [
        (1, "C1", 0.0),
        (2, "C2", 0.0),
        (3, "C3", 0.0),
        (4, "C4", 0.0),
        (5, "C5", 0.0),
        (6, "C6", 0.0),
        (7, "C7", 0.0),
        (8, "D1", 0.0),
        (9, "S1", 0.0),
        (10, "S2", 0.0),
        (11, "S3", 0.0),
        (12, "O1A", 0.0),
        (13, "M3", 0.0),
        (14, "M1", 40.0),
    ],
)
def test_sfc_matches_standalone_reference(grid_value: int, fuel_type: str, percent_conifer: float):
    datasets = make_datasets(
        np.array([[grid_value]]),
        percent_conifer=np.array([[percent_conifer]]),
    )

    result = calculate_primary_fire_behaviour(datasets)

    expected = cffdrs.surface_fuel_consumption.surface_fuel_consumption(
        fuel_type, 90.0, 60.0, percent_conifer, 0.35
    )
    assert result.sfc[0, 0] == pytest.approx(expected)


def test_normalizes_directions_and_clamps_slope_before_primary_fbp(mocker: MockerFixture):
    primary_fbp = mocker.patch(
        "wps_sfms.processors.primary_fire_behaviour.vectorized_primary_fire_behaviour_prediction",
        return_value=SimpleNamespace(
            sfc=np.array([1.0]),
            ros=np.array([2.0]),
            hfi=np.array([3.0]),
            tfc=np.array([4.0]),
            cfb=np.array([0.5]),
        ),
    )

    calculate_primary_fire_behaviour(
        make_datasets(
            np.array([[6.0]]),
            wind_direction=np.array([[450.0]]),
            slope=np.array([[300.0]]),
            aspect=np.array([[410.0]]),
        )
    )

    call_args = primary_fbp.call_args.args
    np.testing.assert_allclose(call_args[4], np.array([np.pi / 2]))
    np.testing.assert_array_equal(call_args[5], np.array([70.0]))
    np.testing.assert_allclose(call_args[6], np.array([np.radians(50.0)]))


def test_aspect_is_irrelevant_when_negative_slope_is_clamped_to_zero():
    negative_slope = make_datasets(
        np.array([[6.0]]), slope=np.array([[-14.0]]), aspect=np.array([[275.0]])
    )
    flat = make_datasets(np.array([[6.0]]), slope=np.array([[0.0]]), aspect=np.array([[0.0]]))

    negative_result = calculate_primary_fire_behaviour(negative_slope)
    flat_result = calculate_primary_fire_behaviour(flat)

    np.testing.assert_allclose(negative_result.ros, flat_result.ros)
    np.testing.assert_allclose(negative_result.hfi, flat_result.hfi)


def test_aspect_nodata_is_preserved_when_slope_is_clamped_to_zero():
    datasets = make_datasets(
        np.array([[6.0, 6.0]]),
        slope=np.array([[0.0, -14.0]]),
        aspect=np.full((1, 2), TEST_INPUT_NODATA),
    )

    result = calculate_primary_fire_behaviour(datasets)

    expected = np.full((1, 2), SFMS_NO_DATA, dtype=np.float32)
    np.testing.assert_array_equal(result.sfc, expected)
    np.testing.assert_array_equal(result.ros, expected)
    np.testing.assert_array_equal(result.hfi, expected)
    np.testing.assert_array_equal(result.tfc, expected)
    np.testing.assert_array_equal(result.cfb, expected)


def test_non_fuel_becomes_zero_and_source_nodata_remains_sfms_nodata():
    datasets = make_datasets(np.array([[99, 102, TEST_INPUT_NODATA]]))

    result = calculate_primary_fire_behaviour(datasets)

    expected = np.array([[0, 0, SFMS_NO_DATA]], dtype=np.float32)
    np.testing.assert_array_equal(result.sfc, expected)
    np.testing.assert_array_equal(result.ros, expected)
    np.testing.assert_array_equal(result.hfi, expected)
    np.testing.assert_array_equal(result.tfc, expected)
    np.testing.assert_array_equal(result.cfb, expected)


def test_non_fuel_becomes_zero_when_other_inputs_are_nodata():
    datasets = make_datasets(
        np.array([[99, 102]]),
        ffmc=np.full((1, 2), TEST_INPUT_NODATA),
        fmc=np.full((1, 2), TEST_INPUT_NODATA),
    )

    result = calculate_primary_fire_behaviour(datasets)

    np.testing.assert_array_equal(result.sfc, np.zeros((1, 2), dtype=np.float32))
    np.testing.assert_array_equal(result.ros, np.zeros((1, 2), dtype=np.float32))
    np.testing.assert_array_equal(result.hfi, np.zeros((1, 2), dtype=np.float32))
    np.testing.assert_array_equal(result.tfc, np.zeros((1, 2), dtype=np.float32))
    np.testing.assert_array_equal(result.cfb, np.zeros((1, 2), dtype=np.float32))


@pytest.mark.parametrize(
    "input_name",
    ["ffmc", "bui", "wind_speed", "wind_direction", "slope", "aspect"],
)
def test_required_input_nodata_becomes_sfms_nodata(input_name: str):
    datasets = make_datasets(
        np.array([[6.0]]),
        **{input_name: np.array([[TEST_INPUT_NODATA]])},
    )

    result = calculate_primary_fire_behaviour(datasets)

    assert result.sfc[0, 0] == SFMS_NO_DATA
    assert result.ros[0, 0] == SFMS_NO_DATA
    assert result.hfi[0, 0] == SFMS_NO_DATA
    assert result.tfc[0, 0] == SFMS_NO_DATA
    assert result.cfb[0, 0] == SFMS_NO_DATA


@pytest.mark.parametrize("fmc", [TEST_INPUT_NODATA, np.nan, 0.0, -1.0, 120.1])
def test_invalid_fmc_becomes_sfms_nodata(fmc: float):
    datasets = make_datasets(np.array([[6.0]]), fmc=np.array([[fmc]]))

    result = calculate_primary_fire_behaviour(datasets)

    assert result.sfc[0, 0] == SFMS_NO_DATA
    assert result.ros[0, 0] == SFMS_NO_DATA
    assert result.hfi[0, 0] == SFMS_NO_DATA
    assert result.tfc[0, 0] == SFMS_NO_DATA
    assert result.cfb[0, 0] == SFMS_NO_DATA


@pytest.mark.parametrize("fmc", [0.1, 120.0])
def test_valid_fmc_boundaries_are_calculated(fmc: float):
    datasets = make_datasets(np.array([[6.0]]), fmc=np.array([[fmc]]))

    result = calculate_primary_fire_behaviour(datasets)

    assert np.isfinite(result.hfi[0, 0])
    assert result.hfi[0, 0] != SFMS_NO_DATA


def test_processor_binds_opened_datasets_by_input_key():
    datasets = make_datasets(np.array([[1]]))
    inputs = make_inputs()
    processor = PrimaryFireBehaviourProcessor(TEST_DATETIME)

    with processor._open_datasets(
        make_dataset_context(datasets, reverse=True), inputs
    ) as opened_datasets:
        assert opened_datasets == datasets


@pytest.mark.anyio
async def test_processor_publishes_five_outputs_with_values_and_metadata(
    mocker: MockerFixture,
    output_mask: WPSDataset,
):
    datasets = make_datasets(np.array([[1]]))
    inputs = make_inputs()
    captured = []
    output_mask.as_gdal_ds().GetRasterBand(1).WriteArray(np.array([[1]], dtype=np.float32))

    async def capture_publish(*, dataset, output_key, **_kwargs):
        band = dataset.as_gdal_ds().GetRasterBand(1)
        captured.append(
            {
                "output_key": output_key,
                "description": band.GetDescription(),
                "unit": band.GetUnitType(),
                "nodata": band.GetNoDataValue(),
                "value": band.ReadAsArray()[0, 0],
            }
        )
        return SimpleNamespace(output_key=output_key, cog_key=f"{output_key}.cog")

    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=True))
    clear_cache = mocker.patch("wps_shared.utils.s3.gdal.VSICurlClearCache")
    mocker.patch(
        "wps_sfms.processors.primary_fire_behaviour.publish_dataset",
        side_effect=capture_publish,
    )
    mocker.patch(
        "wps_sfms.processors.primary_fire_behaviour.calculate_primary_fire_behaviour",
        return_value=PrimaryFireBehaviourResult(
            sfc=np.array([[1.0]], dtype=np.float32),
            ros=np.array([[2.0]], dtype=np.float32),
            hfi=np.array([[3.0]], dtype=np.float32),
            tfc=np.array([[4.0]], dtype=np.float32),
            cfb=np.array([[0.5]], dtype=np.float32),
            nodata_value=SFMS_NO_DATA,
        ),
    )

    await PrimaryFireBehaviourProcessor(TEST_DATETIME).process(
        s3_client, make_dataset_context(datasets), inputs
    )

    assert captured == [
        {
            "output_key": inputs.output_keys[FBPParameter.SFC],
            "description": "surface_fuel_consumption",
            "unit": "kg/m2",
            "nodata": pytest.approx(SFMS_NO_DATA),
            "value": pytest.approx(1.0),
        },
        {
            "output_key": inputs.output_keys[FBPParameter.ROS],
            "description": "rate_of_spread",
            "unit": "m/min",
            "nodata": pytest.approx(SFMS_NO_DATA),
            "value": pytest.approx(2.0),
        },
        {
            "output_key": inputs.output_keys[FBPParameter.HFI],
            "description": "head_fire_intensity",
            "unit": "kW/m",
            "nodata": pytest.approx(SFMS_NO_DATA),
            "value": pytest.approx(3.0),
        },
        {
            "output_key": inputs.output_keys[FBPParameter.TFC],
            "description": "total_fuel_consumption",
            "unit": "kg/m2",
            "nodata": pytest.approx(SFMS_NO_DATA),
            "value": pytest.approx(4.0),
        },
        {
            "output_key": inputs.output_keys[FBPParameter.CFB],
            "description": "crown_fraction_burned",
            "unit": "fraction",
            "nodata": pytest.approx(SFMS_NO_DATA),
            "value": pytest.approx(0.5),
        },
    ]
    clear_cache.assert_called_once_with()


@pytest.mark.anyio
async def test_processor_publish_failure_propagates_and_clears_cache(
    mocker: MockerFixture,
    output_mask: WPSDataset,
):
    datasets = make_datasets(np.array([[1]]))
    inputs = make_inputs()
    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=True))
    processor = PrimaryFireBehaviourProcessor(TEST_DATETIME)
    input_context = make_dataset_context(datasets)
    mocker.patch(
        "wps_sfms.processors.primary_fire_behaviour.publish_dataset",
        new=AsyncMock(side_effect=RuntimeError("COG generation failed")),
    )
    clear_cache = mocker.patch("wps_shared.utils.s3.gdal.VSICurlClearCache")

    with pytest.raises(RuntimeError, match="COG generation failed"):
        await processor.process(s3_client, input_context, inputs)

    clear_cache.assert_called_once_with()


@pytest.mark.anyio
async def test_processor_rejects_mismatched_grid(mocker: MockerFixture):
    datasets = make_datasets(np.array([[1]]))
    inputs = make_inputs()
    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=True))
    processor = PrimaryFireBehaviourProcessor(TEST_DATETIME)
    input_context = make_dataset_context(datasets)
    mocker.patch("wps_sfms.raster_dependencies.rasters_match", return_value=False)
    publish = mocker.patch(
        "wps_sfms.processors.primary_fire_behaviour.publish_dataset", new=AsyncMock()
    )

    with pytest.raises(ValueError, match="does not match the fuel grid"):
        await processor.process(s3_client, input_context, inputs)

    publish.assert_not_awaited()


@pytest.mark.anyio
async def test_processor_rejects_missing_dependency():
    inputs = make_inputs()
    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=False))
    processor = PrimaryFireBehaviourProcessor(TEST_DATETIME)
    datasets = make_datasets(np.array([[1]]))
    input_context = make_dataset_context(datasets)

    with pytest.raises(RuntimeError, match="Missing raster dependencies"):
        await processor.process(s3_client, input_context, inputs)

    s3_client.all_objects_exist.assert_awaited_once_with(
        inputs.fuel_key,
        inputs.ffmc_key,
        inputs.bui_key,
        inputs.wind_speed_key,
        inputs.wind_direction_key,
        inputs.slope_key,
        inputs.aspect_key,
        inputs.percent_conifer_key,
        inputs.fmc_key,
    )
