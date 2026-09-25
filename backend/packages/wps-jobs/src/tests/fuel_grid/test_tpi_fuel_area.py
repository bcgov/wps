from pathlib import Path

import numpy as np
from osgeo import gdal, osr

from wps_shared.db.models.auto_spatial_advisory import TPIClassEnum
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.wps_dataset import Georeference
from fuel_grid.tpi_fuel_area import calculate_masked_tpi_areas


def test_calculate_masked_tpi_areas_groups_raster_values(tmp_path: Path):
    tpi_path = str(tmp_path / "tpi.tif")
    zone_path = str(tmp_path / "zones.tif")
    georeference = Georeference((-10, 2, 0, 10, 0, -2), osr.GetUserInputAsWKT("EPSG:3005"))
    tpi_raster = WPSDataset.from_array(
        np.array([[1, 2, 4], [3, 4, 1]], dtype=np.uint8),
        georeference,
        datatype=gdal.GDT_Byte,
        output_path=tpi_path,
    )
    zone_raster = WPSDataset.from_array(
        np.array([[1, 1, 1], [2, 2, -1]], dtype=np.int16),
        georeference,
        nodata_value=-1,
        datatype=gdal.GDT_Int16,
        output_path=zone_path,
    )
    tpi_raster.close()
    zone_raster.close()

    result = calculate_masked_tpi_areas(tpi_path, zone_path)

    assert result == {
        (1, TPIClassEnum.valley_bottom): 4,
        (1, TPIClassEnum.mid_slope): 4,
        (2, TPIClassEnum.upper_slope): 4,
    }
