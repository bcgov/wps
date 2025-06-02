from osgeo import gdal, ogr
import os
import subprocess

# There are a lot of tippecanoe command line arguments worth exploring. The "--coalesce" option was required when creating
# a pmtiles file from the 500m fuel grid. The 500m fuel grid had too many features per tile and increased tile size above 500KB
# which tippecanoe did not like. The tippecanoe cli suggested a couple of command line options which resulted in the number of
# features in the tile being decreased leading to unacceptable visual artifacts. The "--coalesce" option merges small features
# with identical attributes into larger features with a net result of decreasing tile size a while maintaining the correct
# visual representation of the underlying tif.


def tippecanoe_wrapper(
    geojson_filepath: str, output_pmtiles_filepath: str, min_zoom: int = 4, max_zoom: int = 11
):
    """
    Wrapper for the tippecanoe cli tool

    :param geojson_filepath: Path to input geojson (must be in EPSG:4326)
    :type geojson_filepath: str
    :param output_pmtile: Path to output pmtiles file
    :type output_pmtiles_filepath: str
    :param min_zoom: pmtiles zoom out level
    :type min_zoom: int
    :param max_zoom: pmtiles zoom in level
    :type max_zoom: int
    :param keep_attribute: Attribute to keep in the tiles, the rest will be dropped to save file size.
    :type keep_attribute: str
    """
    cmd = [
        "tippecanoe",
        f"--minimum-zoom={min_zoom}",
        f"--maximum-zoom={max_zoom}",
        "--projection=EPSG:4326",
        f"--output={output_pmtiles_filepath}",
        geojson_filepath,
        "--force",  # overwrite output file if it exists
        "--no-progress-indicator",  # Don't report progress, but still give warnings
        "--coalesce",
        "--reorder",
        "--hilbert",  # put features in Hilbert Curve order instead of the usual Z-Order, should improve spatial coalescing
    ]

    subprocess.run(cmd, check=True)


def write_geojson(polygons: ogr.Layer, output_dir: str) -> str:
    """
    Write geojson file, projected in EPSG:4326, from ogr.Layer object

    :param polygons: Polygon layer
    :type polygons: ogr.Layer
    :param output_dir: Output directory
    :type output_dir: str
    :return: Path to geojson file
    :rtype: str
    """
    # We can't use an in-memory layer for translating, so we'll create a temp layer
    # Using a geopackage since it supports all projections and doesn't limit field name lengths.
    temp_gpkg = os.path.join(output_dir, "temp_polys.gpkg")
    driver = ogr.GetDriverByName("GPKG")
    temp_data_source = driver.CreateDataSource(temp_gpkg)
    temp_data_source.CopyLayer(polygons, "poly_layer")

    # We need a geojson file to pass to tippecanoe
    temp_geojson = os.path.join(output_dir, "temp_polys.geojson")

    # tippecanoe recommends the input geojson be in EPSG:4326 [https://github.com/felt/tippecanoe#projection-of-input]
    gdal.VectorTranslate(
        destNameOrDestDS=temp_geojson,
        srcDS=temp_gpkg,
        format="GeoJSON",
        dstSRS="EPSG:4326",
        reproject=True,
    )

    del temp_gpkg

    return temp_geojson
