import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

import numpy as np
import pytest
from osgeo import gdal

import wps_sfms.processors.wind as wind_module
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.schemas.sfms import SFMSDaily
from wps_sfms.interpolation.field import build_wind_vector_field
from wps_sfms.processors.idw import ValidPixelIDWResult
from wps_sfms.processors.wind import WindDirectionInterpolator
from wps_sfms.tests.conftest import create_test_raster

TEST_FOR_DATETIME = datetime(2025, 7, 15, 20, tzinfo=timezone.utc)
TEST_EXTENT = (-123.1, -123.0, 49.0, 49.1)


def make_wind_daily(
    code: int,
    lat: float,
    lon: float,
    wind_speed: float,
    wind_direction: float | None,
) -> SFMSDaily:
    return SFMSDaily(
        code=code,
        for_datetime=TEST_FOR_DATETIME,
        run_type=RunTypeEnum.actual,
        lat=lat,
        lon=lon,
        wind_speed=wind_speed,
        wind_direction=wind_direction,
    )


def make_paired_wind_dailies() -> list[SFMSDaily]:
    return [
        make_wind_daily(100, 49.05, -123.05, 10.0, 90.0),
        make_wind_daily(101, 49.08, -123.02, 8.0, 180.0),
    ]


@contextmanager
def reference_and_mask_rasters(size: int):
    test_id = uuid.uuid4().hex
    ref_path = f"/vsimem/reference_{test_id}.tif"
    mask_path = f"/vsimem/mask_{test_id}.tif"

    try:
        create_test_raster(ref_path, size, size, TEST_EXTENT, fill_value=1.0)
        create_test_raster(mask_path, size, size, TEST_EXTENT, fill_value=1.0)
        yield ref_path, mask_path
    finally:
        gdal.Unlink(ref_path)
        gdal.Unlink(mask_path)


class TestWindDirectionInterpolator:
    def test_compute_direction_from_uv_matches_legacy_special_cases(self):
        u = np.array([-1.0, 1.0, 0.0], dtype=np.float32)
        v = np.array([0.0, 0.0, 0.0], dtype=np.float32)

        direction = WindDirectionInterpolator.compute_direction_from_uv(u, v)

        np.testing.assert_allclose(direction, np.array([90.0, 270.0, 0.0], dtype=np.float32))

    def test_compute_direction_from_uv_uses_arctan_branch_when_v_nonzero(self):
        # Four quadrants with v != 0 should follow: deg(atan2(u, v)) + 180
        u = np.array([1.0, -1.0, 1.0, -1.0], dtype=np.float32)
        v = np.array([1.0, 1.0, -1.0, -1.0], dtype=np.float32)

        direction = WindDirectionInterpolator.compute_direction_from_uv(u, v)

        np.testing.assert_allclose(
            direction,
            np.array([225.0, 135.0, 315.0, 45.0], dtype=np.float32),
            atol=1e-5,
        )

    def test_compute_direction_from_uv_mixed_zero_and_nonzero_v(self):
        # Mixed inputs should apply atan2 where v != 0 and legacy overrides where v == 0.
        u = np.array([1.0, -1.0, 0.0], dtype=np.float32)
        v = np.array([1.0, 0.0, 0.5], dtype=np.float32)

        direction = WindDirectionInterpolator.compute_direction_from_uv(u, v)

        np.testing.assert_allclose(
            direction,
            np.array([225.0, 90.0, 180.0], dtype=np.float32),
            atol=1e-5,
        )

    def test_interpolate_basic_success(self):
        with reference_and_mask_rasters(size=10) as (ref_path, mask_path):
            actuals = make_paired_wind_dailies()
            field = build_wind_vector_field(actuals)

            dataset = WindDirectionInterpolator(mask_path=mask_path, field=field).interpolate(
                ref_path
            )
            data = dataset.ds.GetRasterBand(1).ReadAsArray()
            nodata = dataset.ds.GetRasterBand(1).GetNoDataValue()
            valid = data[data != nodata]

            assert valid.size > 0
            assert np.all(valid >= 0.0)
            assert np.all(valid <= 360.0)

    def test_interpolate_raises_without_paired_stations(self):
        with reference_and_mask_rasters(size=5) as (ref_path, mask_path):
            actuals = [make_wind_daily(100, 49.05, -123.05, 10.0, None)]
            field = build_wind_vector_field(actuals)

            with pytest.raises(RuntimeError, match="No pixels were successfully interpolated"):
                WindDirectionInterpolator(mask_path=mask_path, field=field).interpolate(ref_path)

    @pytest.mark.parametrize("successful_component_label", ["wind-u component", "wind-v component"])
    def test_interpolate_raises_when_only_one_component_succeeds(
        self, monkeypatch, successful_component_label
    ):
        with reference_and_mask_rasters(size=5) as (ref_path, mask_path):
            actuals = make_paired_wind_dailies()
            field = build_wind_vector_field(actuals)

            def _fake_idw_on_valid_pixels(**kwargs):
                valid_yi = kwargs["valid_yi"]
                valid_xi = kwargs["valid_xi"]
                total_pixels = kwargs["total_pixels"]
                label = kwargs["label"]
                n = len(valid_yi)

                if label == successful_component_label:
                    interpolated_values = np.full(n, 4.0, dtype=np.float32)
                    succeeded_mask = np.ones(n, dtype=bool)
                else:
                    interpolated_values = np.full(n, np.nan, dtype=np.float32)
                    succeeded_mask = np.zeros(n, dtype=bool)

                return ValidPixelIDWResult(
                    interpolated_values=interpolated_values,
                    succeeded_mask=succeeded_mask,
                    rows=valid_yi[succeeded_mask],
                    cols=valid_xi[succeeded_mask],
                    values=interpolated_values[succeeded_mask].astype(np.float32, copy=False),
                    total_pixels=total_pixels,
                    interpolated_count=int(np.sum(succeeded_mask)),
                    failed_interpolation_count=n - int(np.sum(succeeded_mask)),
                    skipped_nodata_count=total_pixels - n,
                )

            monkeypatch.setattr(wind_module, "idw_on_valid_pixels", _fake_idw_on_valid_pixels)

            with pytest.raises(RuntimeError, match="No pixels were successfully interpolated"):
                WindDirectionInterpolator(mask_path=mask_path, field=field).interpolate(ref_path)
