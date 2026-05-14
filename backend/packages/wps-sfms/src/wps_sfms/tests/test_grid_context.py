import uuid

import numpy as np
import pytest
from osgeo import gdal

from wps_sfms.interpolation.grid import build_grid_context
from wps_sfms.tests.conftest import create_test_raster


class TestBuildGridContext:
    def test_loads_masked_grid_with_dem_and_temperature(self):
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        temp_path = f"/vsimem/temp_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(dem_path, 5, 5, extent, fill_value=100.0)
            create_test_raster(temp_path, 5, 5, extent, fill_value=15.0)

            mask_data = np.full((5, 5), 1.0, dtype=np.float32)
            mask_data[2, 2] = 0.0
            create_test_raster(mask_path, 5, 5, extent, data=mask_data)

            grid = build_grid_context(
                ref_path,
                mask_path,
                dem_path=dem_path,
                temperature_raster_path=temp_path,
            )

            assert grid.x_size == 5
            assert grid.y_size == 5
            assert grid.total_pixels == 25
            assert grid.skipped_nodata_count == 1
            assert len(grid.valid_yi) == 24
            assert grid.valid_dem_values is not None
            assert grid.temperature_data is not None
            assert grid.valid_dem_values.shape == (24,)
            assert grid.temperature_data.shape == (5, 5)
            assert grid.valid_lats.dtype == np.float32
            assert grid.valid_lons.dtype == np.float32
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(mask_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(temp_path)

    def test_raises_when_dem_grid_does_not_match_reference(self):
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(mask_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(dem_path, 4, 5, extent, fill_value=100.0)

            with pytest.raises(ValueError, match="DEM grid does not match reference raster"):
                build_grid_context(ref_path, mask_path, dem_path=dem_path)
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(mask_path)
            gdal.Unlink(dem_path)
