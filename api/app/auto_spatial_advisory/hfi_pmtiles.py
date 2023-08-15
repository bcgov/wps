from osgeo import gdal, ogr
import os
import subprocess


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
        '--force'
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
    temp_gpkg = os.path.join(output_dir, 'temp_hfi_polys.gpkg')
    driver = ogr.GetDriverByName('GPKG')
    temp_data_source = driver.CreateDataSource(temp_gpkg)
    temp_data_source.CopyLayer(hfi_polygons, 'hfi_layer')

    # We need a geojson file to pass to tippecanoe
    temp_geojson = os.path.join(output_dir, 'temp_hfi_polys.geojson')

    # tippecanoe recommends the input geojson be in EPSG:4326 [https://github.com/felt/tippecanoe#projection-of-input]
    # We also don't need hfi values below 1 (currently we don't even show values below 4000)
    gdal.VectorTranslate(destNameOrDestDS=temp_geojson, srcDS=temp_gpkg,
                         format='GeoJSON', dstSRS='EPSG:4326', reproject=True, where='hfi > 0')

    del temp_gpkg

    return temp_geojson
