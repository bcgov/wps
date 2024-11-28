from tempfile import TemporaryDirectory

from app.utils.pmtiles import tippecanoe_wrapper, write_geojson
from app.utils.polygonize import polygonize_in_memory


def generate_fuel_pmtiles(fuel_grid_path: str, output_path: str):
    """
    Simple function for local use to regenerate fuel grid pmtiles annually when the new fuel grid raster
    is received from BCWS Geospatial. Typically stored in s3: {bucket}/psu/pmtiles/fuel
    """
    with polygonize_in_memory(fuel_grid_path, "fuel", "fuel") as layer, TemporaryDirectory() as temp_dir:
        temp_geojson = write_geojson(layer, temp_dir)

        tippecanoe_wrapper(temp_geojson, output_path, min_zoom=4, max_zoom=12)


def main():
    fuel_grid = "/path/to/fbp2024.tif"
    output_path = "/output/to/fbp2024.pmtiles"

    generate_fuel_pmtiles(fuel_grid, output_path)


if __name__ == "__main__":
    main()
