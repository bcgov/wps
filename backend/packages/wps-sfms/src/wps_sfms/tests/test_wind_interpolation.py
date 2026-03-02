import uuid

import numpy as np
import pytest
from osgeo import gdal

from wps_shared.schemas.sfms import SFMSDailyActual
from wps_sfms.interpolation.source import StationWindVectorSource
from wps_sfms.processors.wind import WindDirectionInterpolator
from wps_sfms.tests.conftest import create_test_raster


class TestWindDirectionInterpolator:
    def test_compute_direction_from_uv_matches_legacy_special_cases(self):
        u = np.array([-1.0, 1.0, 0.0], dtype=np.float32)
        v = np.array([0.0, 0.0, 0.0], dtype=np.float32)

        direction = WindDirectionInterpolator.compute_direction_from_uv(u, v)

        np.testing.assert_allclose(direction, np.array([90.0, 270.0, 0.0], dtype=np.float32))

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
