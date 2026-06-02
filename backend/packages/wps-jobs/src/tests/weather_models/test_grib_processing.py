"""Tests for grib file processing"""

import logging
import os
from operator import itemgetter

import pytest
import weather_model_jobs.utils.process_grib as process_grib
from osgeo import gdal
from pyproj import CRS
from wps_shared.geospatial.geospatial import NAD83_CRS

logger = logging.getLogger(__name__)


def open_grib_file(filename: str):
    """Open the dataset."""
    grib_path = get_grib_file_path(filename)
    return gdal.Open(grib_path)


def get_grib_file_path(filename: str):
    dirname = os.path.dirname(os.path.realpath(__file__))
    grib_path = os.path.join(dirname, filename)
    return grib_path


@pytest.mark.parametrize(
    "filename,origin,pixel_size",
    [
        (
            "20260602T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT000H.grib2",
            (-180.075, 90.075),
            (0.15, -0.15),
        ),
    ],
)
def test_get_dataset_geometry(filename, origin, pixel_size):
    grib_path = get_grib_file_path(filename)
    dataset_geometry = process_grib.get_dataset_transform(grib_path)
    geotransform = dataset_geometry.to_gdal()
    actual_origin = itemgetter(0, 3)(geotransform)
    actual_pixel_size = itemgetter(1, 5)(geotransform)
    assert actual_origin == origin
    assert actual_pixel_size == pixel_size


@pytest.mark.parametrize(
    "filename,geographic_coordinate,raster_coordinate,expected_value",
    [
        (
            "20260602T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT000H.grib2",
            [-120.4816667, 50.6733333],
            (397, 262),
            17.5934692382813,
        ),
        (
            "20260602T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT000H.grib2",
            [-116.7464000, 49.4358000],
            (422, 270),
            7.39345703125002,
        ),
        (
            "20260602T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT000H.grib2",
            [-123.2732667, 52.0837700],
            (378, 253),
            21.8934570312500,
        ),
        (
            "20230317T18Z_MSC_HRDPS_RH_AGL-2m_RLatLon0.0225_PT001H.grib2",
            [-120.4816667, 50.6733333],
            (496, 879),
            49.6418838500977,
        ),
        (
            "20230317T18Z_MSC_HRDPS_RH_AGL-2m_RLatLon0.0225_PT001H.grib2",
            [-116.7464000, 49.4358000],
            (599, 940),
            41.9403686523438,
        ),
        (
            "20230317T18Z_MSC_HRDPS_RH_AGL-2m_RLatLon0.0225_PT001H.grib2",
            [-123.2732667, 52.0837700],
            (425, 809),
            57.5278663635254,
        ),
    ],
)
def test_calculate_raster_coordinates(
    filename, geographic_coordinate, raster_coordinate, expected_value
):
    grib_path = get_grib_file_path(filename)
    dataset = gdal.Open(grib_path, gdal.GA_ReadOnly)
    proj_crs = CRS.from_string(dataset.GetProjection())
    transformer = process_grib.get_transformer(NAD83_CRS, proj_crs)
    padf_transform = process_grib.get_dataset_transform(grib_path)
    longitude, latitude = geographic_coordinate
    actual_raster_coordinate = process_grib.calculate_raster_coordinate(
        longitude, latitude, padf_transform, transformer
    )
    assert actual_raster_coordinate == raster_coordinate

    x_coordinate, y_coordinate = actual_raster_coordinate
    assert 0 <= x_coordinate < dataset.RasterXSize
    assert 0 <= y_coordinate < dataset.RasterYSize

    value = dataset.GetRasterBand(1).ReadAsArray(
        x_coordinate, y_coordinate, 1, 1
    )[0, 0]
    assert value == pytest.approx(expected_value)
