import os
import sys
import json
import tempfile
import numpy as np
from osgeo import gdal, ogr
from pyproj import Transformer, Proj
from shapely.ops import transform
from shapely.geometry import shape, mapping


def _create_in_memory_band(data: np.ndarray, cols, rows, projection, geotransform):
    """ Create an in memory data band to represent a single raster layer.
    See https://gdal.org/user/raster_data_model.html#raster-band for a complete
    description of what a raster band is.
    """
    mem_driver = gdal.GetDriverByName('MEM')

    dataset = mem_driver.Create('memory', cols, rows, 1, gdal.GDT_Byte)
    dataset.SetProjection(projection)
    dataset.SetGeoTransform(geotransform)
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)

    return dataset, band


def _re_project_and_classify_geojson(source_json_filename: str,
                                     source_projection: str) -> dict:
    proj_from = Proj(projparams=source_projection)
    proj_to = Proj('epsg:4326')
    project = Transformer.from_proj(proj_from, proj_to, always_xy=True)
    with open(source_json_filename, encoding="utf-8") as source_file:
        geojson_data = json.load(source_file)

        for feature in geojson_data.get('features', {}):
            properties = feature.get('properties', {})
            hfi = properties.get('hfi', None)
            if hfi is not None:
                if hfi == 1:
                    properties['hfi'] = '4000 > hfi < 10000'
                elif hfi == 2:
                    properties['hfi'] = 'hfi >= 10000'
            # Re-project to WGS84
            source_geometry = shape(feature['geometry'])
            geometry = transform(project.transform, source_geometry)
            geojson_geometry = mapping(geometry)
            feature['geometry']['coordinates'] = geojson_geometry['coordinates']
    return geojson_data


def polygonize(geotiff_filename, geojson_filename):
    classification = gdal.Open(geotiff_filename, gdal.GA_ReadOnly)
    band = classification.GetRasterBand(1)
    classification_data = band.ReadAsArray()

    # generate mask data
    mask_data = np.where(classification_data == 0, False, True)
    mask_ds, mask_band = _create_in_memory_band(
        mask_data, band.XSize, band.YSize, classification.GetProjection(),
        classification.GetGeoTransform())

    # Create a GeoJSON layer.
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_filename = os.path.join(temp_dir, 'temp.geojson')
        geojson_driver = ogr.GetDriverByName('GeoJSON')
        dst_ds = geojson_driver.CreateDataSource(temp_filename)
        dst_layer = dst_ds.CreateLayer('hfi')
        field_name = ogr.FieldDefn("hfi", ogr.OFTInteger)
        field_name.SetWidth(24)
        dst_layer.CreateField(field_name)

        # Turn the rasters into polygons.
        gdal.Polygonize(band, mask_band, dst_layer, 0, [], callback=None)

        # Ensure that all data in the target dataset is written to disk.
        dst_ds.FlushCache()
        source_projection = classification.GetProjection()
        # Explicitly clean up (is this needed?)
        del dst_ds, classification, mask_band, mask_ds

        data = _re_project_and_classify_geojson(temp_filename, source_projection)

        # Remove any existing target file.
        if os.path.exists(geojson_filename):
            os.remove(geojson_filename)
        with open(geojson_filename, 'w') as file_pointer:
            json.dump(data, file_pointer, indent=2)


if __name__ == '__main__':
    polygonize(sys.argv[1], sys.argv[2])
