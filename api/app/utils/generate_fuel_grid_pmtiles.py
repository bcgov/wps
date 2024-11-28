from tempfile import TemporaryDirectory

from app import config
from app.utils.pmtiles import tippecanoe_wrapper, write_geojson
from app.utils.polygonize import polygonize_in_memory
from app.utils.s3 import set_s3_gdal_config


def generate_fuel_pmtiles(fuel_grid_path: str, output_path: str):
    """
    Simple function for local use to regenerate fuel grid pmtiles annually when the new fuel grid raster
    is received from BCWS Geospatial. Typically stored in s3: {bucket}/psu/pmtiles/fuel
    """
    set_s3_gdal_config()
    with polygonize_in_memory(fuel_grid_path, "fuel", "fuel") as layer, TemporaryDirectory() as temp_dir:
        temp_geojson = write_geojson(layer, temp_dir)

        tippecanoe_wrapper(temp_geojson, output_path, min_zoom=4, max_zoom=12)


def main():
    bucket = config.get("OBJECT_STORE_BUCKET")
    fuel_grid = f"/vsis3/{bucket}/sfms/static/fbp2024.tif"  # input fuel grid stored in s3
    output_path = "/output/to/fbp2024.pmtiles"  # local output

    generate_fuel_pmtiles(fuel_grid, output_path)


if __name__ == "__main__":
    main()
