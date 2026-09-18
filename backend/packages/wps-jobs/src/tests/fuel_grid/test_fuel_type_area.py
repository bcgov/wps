from pathlib import Path

import numpy as np
from osgeo import gdal, osr

from fuel_grid.fuel_type_area import (
    calculate_fuel_type_areas_per_zone,
)
from wps_shared.geospatial.wps_dataset import Georeference, WPSDataset


def test_calculate_fuel_type_areas_per_zone_groups_raster_values(tmp_path: Path):
    fuel_path = str(tmp_path / "fuel.tif")
    zone_path = str(tmp_path / "zones.tif")
    georeference = Georeference((-10, 2, 0, 10, 0, -2), osr.GetUserInputAsWKT("EPSG:3005"))
    fuel_raster = WPSDataset.from_array(
        np.array([[1, 99, 0], [2, 3, 100]], dtype=np.uint8),
        georeference,
        datatype=gdal.GDT_Byte,
        output_path=fuel_path,
    )
    zone_raster = WPSDataset.from_array(
        np.array([[1, 1, 1], [2, -1, 2]], dtype=np.int16),
        georeference,
        nodata_value=-1,
        datatype=gdal.GDT_Int16,
        output_path=zone_path,
    )
    fuel_raster.close()
    zone_raster.close()

    result = calculate_fuel_type_areas_per_zone(fuel_path, zone_path)

    assert result == {(1, 1): 4, (2, 2): 4}
