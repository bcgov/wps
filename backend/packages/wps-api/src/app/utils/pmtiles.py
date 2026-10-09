from osgeo import gdal, ogr
import json
import os
import struct
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


# A vector tile holding one empty "hfi" layer (version 2, extent 4096), encoded by hand.
_EMPTY_MVT = b"\x1a\x0a\x0a\x03hfi\x28\x80\x20\x78\x02"
# Root directory with one entry pointing tile id 0 (z0) at _EMPTY_MVT: count, tile id delta,
# run length, length, offset + 1. The pmtiles JS reader rejects empty directories.
_EMPTY_ROOT_DIRECTORY = bytes([1, 0, 1, len(_EMPTY_MVT), 1])
_HEADER_LENGTH = 127


def write_empty_pmtiles(output_pmtiles_filepath: str, min_zoom: int = 4, max_zoom: int = 11):
    """
    Write a valid PMTiles v3 archive with no features. tippecanoe refuses empty input, so
    this is used when there is nothing to tile. Its only tile is at z0, below min_zoom, so
    clients never request it and every tile in range comes back empty.

    :param output_pmtiles_filepath: Path to output pmtiles file
    :param min_zoom: pmtiles zoom out level
    :param max_zoom: pmtiles zoom in level
    """
    metadata = json.dumps(
        {"vector_layers": [{"id": "hfi", "fields": {}, "minzoom": min_zoom, "maxzoom": max_zoom}]}
    ).encode()
    root_offset = _HEADER_LENGTH
    metadata_offset = root_offset + len(_EMPTY_ROOT_DIRECTORY)
    tile_data_offset = metadata_offset + len(metadata)
    # BC bounding box, in degrees * 1e7
    min_lon, min_lat, max_lon, max_lat = -1390600000, 483000000, -1140300000, 600000000
    header = struct.pack(
        "<7sB11Q6B4iB2i",
        b"PMTiles",
        3,  # spec version
        root_offset,
        len(_EMPTY_ROOT_DIRECTORY),
        metadata_offset,
        len(metadata),
        tile_data_offset,  # leaf directories offset
        0,  # leaf directories length
        tile_data_offset,
        len(_EMPTY_MVT),
        1,  # addressed tiles
        1,  # tile entries
        1,  # tile contents
        1,  # clustered
        1,  # internal compression: none
        1,  # tile compression: none
        1,  # tile type: mvt
        min_zoom,
        max_zoom,
        min_lon,
        min_lat,
        max_lon,
        max_lat,
        min_zoom,  # center zoom
        (min_lon + max_lon) // 2,
        (min_lat + max_lat) // 2,
    )
    with open(output_pmtiles_filepath, "wb") as f:
        f.write(header + _EMPTY_ROOT_DIRECTORY + metadata + _EMPTY_MVT)


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
    # Close to flush the geopackage to disk before VectorTranslate reopens it by path
    temp_data_source = None

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

    return temp_geojson
