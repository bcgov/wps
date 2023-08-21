from osgeo import gdal, ogr
import os
import subprocess
from app.auto_spatial_advisory.run_type import RunType
from datetime import date


def tippecanoe_wrapper(geojson_filepath: str, output_pmtiles_filepath: str, min_zoom: int = 4, max_zoom: int = 11):
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
    subprocess.run([
        'tippecanoe',
        f'--minimum-zoom={min_zoom}',
        f'--maximum-zoom={max_zoom}',
        '--projection=EPSG:4326',
        f'--output={output_pmtiles_filepath}',
        f'{geojson_filepath}',
        '--force',
        '--quiet'
    ], check=True
    )


def write_hfi_geojson(hfi_polygons: ogr.Layer, output_dir: str) -> str:
    """
    Write geojson file, projected in EPSG:4326, from ogr.Layer object

    :param hfi_polygons: HFI polygon layer
    :type hfi_polygons: ogr.Layer
    :param output_dir: Output directory
    :type output_dir: str
    :return: Path to hfi geojson file
    :rtype: str
    """
    # We can't use an in-memory layer for translating, so we'll create a temp layer
    # Using a geopackage since it supports all projections and doesn't limit field name lengths.
    # This matters because the hfi data is distributed in an odd projection that doesn't have an EPSG code
    temp_gpkg = os.path.join(output_dir, 'temp_hfi_polys.gpkg')
    driver = ogr.GetDriverByName('GPKG')
    temp_data_source = driver.CreateDataSource(temp_gpkg)
    temp_data_source.CopyLayer(hfi_polygons, 'hfi_layer')

    # We need a geojson file to pass to tippecanoe
    temp_geojson = os.path.join(output_dir, 'temp_hfi_polys.geojson')

    # tippecanoe recommends the input geojson be in EPSG:4326 [https://github.com/felt/tippecanoe#projection-of-input]
    gdal.VectorTranslate(destNameOrDestDS=temp_geojson, srcDS=temp_gpkg,
                         format='GeoJSON', dstSRS='EPSG:4326', reproject=True)

    del temp_gpkg

    return temp_geojson


def get_pmtiles_filepath(run_date: date, run_type: RunType, filename: str) -> str:
    """
    Get the file path for both reading and writing the pmtiles from/to the object store.
    Example: {bucket}/sfms/upload/actual/[issue/run_date]/hfi[for_date].pmtiles


    :param run_date: The date of the run to process. (when was the hfi file created?)
    :type run_date: date
    :param run_type: forecast or actual
    :type run_type: RunType
    :param filename: hfi[for_date].pmtiles -> hfi20230821.pmtiles
    :type filename: str
    :return: s3 bucket key for pmtiles file
    :rtype: str
    """
    pmtiles_filepath = os.path.join('psu', 'pmtiles', 'hfi', run_type.value, run_date.strftime('%Y-%m-%d'), filename)

    return pmtiles_filepath
