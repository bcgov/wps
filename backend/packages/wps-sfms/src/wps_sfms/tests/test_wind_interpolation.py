import uuid

import numpy as np
import pytest
from osgeo import gdal

import wps_sfms.processors.wind as wind_module
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_sfms.interpolation.source import StationWindVectorSource
from wps_sfms.processors.idw import ValidPixelIDWResult
from wps_sfms.processors.wind import WindDirectionInterpolator
from wps_sfms.tests.conftest import create_test_raster


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
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 10, 10, extent, fill_value=1.0)
            create_test_raster(mask_path, 10, 10, extent, fill_value=1.0)

            actuals = [
                SFMSDailyActual(
                    code=100, lat=49.05, lon=-123.05, wind_speed=10.0, wind_direction=90.0
                ),
                SFMSDailyActual(
                    code=101, lat=49.08, lon=-123.02, wind_speed=8.0, wind_direction=180.0
                ),
            ]
            source = StationWindVectorSource(actuals)

            dataset = WindDirectionInterpolator(mask_path=mask_path).interpolate(source, ref_path)
            data = dataset.ds.GetRasterBand(1).ReadAsArray()
            nodata = dataset.ds.GetRasterBand(1).GetNoDataValue()
            valid = data[data != nodata]

            assert valid.size > 0
            assert np.all(valid >= 0.0)
            assert np.all(valid <= 360.0)
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(mask_path)

    def test_interpolate_raises_without_paired_stations(self):
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(mask_path, 5, 5, extent, fill_value=1.0)

            actuals = [
                SFMSDailyActual(
                    code=100, lat=49.05, lon=-123.05, wind_speed=10.0, wind_direction=None
                )
            ]
            source = StationWindVectorSource(actuals)

            with pytest.raises(RuntimeError, match="No pixels were successfully interpolated"):
                WindDirectionInterpolator(mask_path=mask_path).interpolate(source, ref_path)
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(mask_path)

    @pytest.mark.parametrize("successful_component_label", ["wind-u component", "wind-v component"])
    def test_interpolate_raises_when_only_one_component_succeeds(
        self, monkeypatch, successful_component_label
    ):
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(mask_path, 5, 5, extent, fill_value=1.0)

            actuals = [
                SFMSDailyActual(
                    code=100, lat=49.05, lon=-123.05, wind_speed=10.0, wind_direction=90.0
                ),
                SFMSDailyActual(
                    code=101, lat=49.08, lon=-123.02, wind_speed=8.0, wind_direction=180.0
                ),
            ]
            source = StationWindVectorSource(actuals)

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
                WindDirectionInterpolator(mask_path=mask_path).interpolate(source, ref_path)
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(mask_path)
