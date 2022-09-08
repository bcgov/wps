"""
    You can take the GeoJSON, and stick it into PostGIS:

    ```bash
    ogr2ogr -f "PostgreSQL" PG:"dbname=tileserv host=localhost user=tileserv password=tileserv"\
             "hfi_classified.json" -nlt MULTIPOLYGON -lco precision=NO -nln hfi -overwrite
    ```

    You could throw it into a development database on openshift, by port forwarding there:

    ```bash
    oc port-forward my-database-pod 5432:5432
    ```

    You can then take something like pg_tileserv to serve it up:

    Download the latest [pg_tileserver](https://github.com/CrunchyData/pg_tileserv), unzip and
    start.

    ```bash
    mkdir pg_tileserv
    cd pg_tileserv
    wget https://postgisftw.s3.amazonaws.com/pg_tileserv_latest_linux.zip
    unzip pg_tileserv
    export DATABASE_URL=postgresql://tileserv:tileserv@localhost/tileserv
    ./pg_tileserv
    ```
"""
import os
import json
import sys
import tempfile
from datetime import date
import numpy as np
from osgeo import gdal, ogr


def _create_in_memory_band(data: np.ndarray, cols, rows, projection, geotransform):
    """ Create an in memory (https://gdal.org/drivers/raster/mem.html) data band to represent a
    single raster layer.
    See https://gdal.org/user/raster_data_model.html#raster-band for a complete
    description of what a raster band is.    
    """
    # Create "In Memory Raster" driver, see: https://gdal.org/drivers/raster/mem.html
    mem_driver = gdal.GetDriverByName('MEM')
    # https://gdal.org/api/python/osgeo.gdal.html#osgeo.gdal.Driver.Create
    # https://gdal.org/api/gdaldriver_cpp.html#_CPPv4N10GDALDriver6CreateEPKciii12GDALDataType12CSLConstList
    # The dataset wants a name, so we give it one, it can be anything, we don't reference it later.
    dataset = mem_driver.Create('memory', cols, rows, 1, gdal.GDT_Byte)
    dataset.SetProjection(projection)
    dataset.SetGeoTransform(geotransform)
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)

    return dataset, band


def classify_geojson(source_json_filename: str, today: date) -> dict:
    with open(source_json_filename, encoding="utf-8") as source_file:
        geojson_data = json.load(source_file)

        for feature in geojson_data.get('features', {}):
            properties = feature.get('properties', {})
            properties['date'] = today.isoformat()
            hfi = properties.get('hfi', None)
            if hfi is not None:
                if hfi == 1:
                    properties['hfi'] = '4000 < hfi < 10000'
                elif hfi == 2:
                    properties['hfi'] = 'hfi >= 10000'
    return geojson_data


def polygonize(geotiff_filename, geojson_filename, today: date):
    classification = gdal.Open(geotiff_filename, gdal.GA_ReadOnly)

    warp = gdal.Warp('hfi_wgs84.tiff', classification, dstSRS='EPSG:4326')
    warp = None  # Closes the file so its written to disk
    del classification, warp

    wgs84_classification = gdal.Open('hfi_wgs84.tiff', gdal.GA_ReadOnly)
    band = wgs84_classification.GetRasterBand(1)
    classification_data = wgs84_classification.ReadAsArray()

    # generate mask data
    mask_data = np.where(classification_data == 0, False, True)
    mask_ds, mask_band = _create_in_memory_band(
        mask_data, band.XSize, band.YSize, wgs84_classification.GetProjection(),
        wgs84_classification.GetGeoTransform())

    # Create a GeoJSON layer.
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_filename = os.path.join(temp_dir, 'temp.geojson')
        geojson_driver = ogr.GetDriverByName('GeoJSON')
        dst_ds = geojson_driver.CreateDataSource(temp_filename)

        # HFI Layer
        dst_layer = dst_ds.CreateLayer('hfi')
        field_name = ogr.FieldDefn("hfi", ogr.OFTInteger)
        field_name.SetWidth(24)
        dst_layer.CreateField(field_name)

        # Turn the rasters into polygons.
        gdal.Polygonize(band, mask_band, dst_layer, 0, [], callback=None)

        # Ensure that all data in the target dataset is written to disk.
        dst_ds.FlushCache()
        # Explicitly clean up (is this needed?)
        del dst_ds, mask_band, mask_ds

        data = classify_geojson(temp_filename, today)

        # Remove any existing target file.
        if os.path.exists(geojson_filename):
            os.remove(geojson_filename)
        with open(geojson_filename, 'w', encoding='utf-8') as file_pointer:
            json.dump(data, file_pointer, indent=2)


if __name__ == '__main__':
    polygonize(sys.argv[1], sys.argv[2], date.fromisoformat(sys.argv[3]))
