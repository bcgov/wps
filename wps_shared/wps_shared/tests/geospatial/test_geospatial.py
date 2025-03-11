from affine import Affine
import os
import pytest
from pyproj import CRS
from wps_shared.geospatial.geospatial import NAD83_CRS, calculate_geographic_coordinate, get_transformer

def read_file_contents(filename):
    """Given a filename, return json"""
    dirname = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dirname, filename), "r") as file:
        return file.read()

@pytest.mark.parametrize(
    "geotransform,wkt_projection_string,raster_coordinate,geographic_coordinate",
    [
        ([-2099127.494496938, 2500.0, 0.0, -2099388.521499629, 0.0, -2500.0], "CMC_hrdps_continental_ps2.5km_projection_wkt.txt", [472, 819], (-120.49716122617183, 50.67953463749049)),
        ([-2099127.494496938, 2500.0, 0.0, -2099388.521499629, 0.0, -2500.0], "CMC_hrdps_continental_ps2.5km_projection_wkt.txt", [572, 897], (-116.7609172273627, 49.43970905337442)),
        ([-2099127.494496938, 2500.0, 0.0, -2099388.521499629, 0.0, -2500.0], "CMC_hrdps_continental_ps2.5km_projection_wkt.txt", [409, 736], (-123.28555732697632, 52.084540312301314)),
        ([-180.075, 0.15000000000000002, 0.0, 90.075, 0.0, -0.15], "CMC_glb_latlon.15x.15_projection_wkt.txt", [370, 330], (-124.57499999999999, 40.575)),
        ([-180.075, 0.15000000000000002, 0.0, 90.075, 0.0, -0.15], "CMC_glb_latlon.15x.15_projection_wkt.txt", [315, 455], (-132.825, 21.825000000000003)),
        ([-180.075, 0.15000000000000002, 0.0, 90.075, 0.0, -0.15], "CMC_glb_latlon.15x.15_projection_wkt.txt", [427, 245], (-116.02499999999998, 53.325)),
    ],
)
def test_calculate_geographic_coordinate(geotransform, wkt_projection_string, raster_coordinate, geographic_coordinate):
    wkt_string = read_file_contents(wkt_projection_string)
    proj_crs = CRS.from_string(wkt_string)
    transformer = get_transformer(proj_crs, NAD83_CRS)
    padf_transform = Affine.from_gdal(*geotransform)
    calculated_geographic_coordinate = calculate_geographic_coordinate(raster_coordinate, padf_transform, transformer)
    assert calculated_geographic_coordinate == geographic_coordinate