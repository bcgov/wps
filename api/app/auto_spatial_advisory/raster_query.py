from osgeo import gdal, ogr, osr
from app import config
from app.auto_spatial_advisory.common import get_s3_key
gdal.UseExceptions()

def set_gdal_s3_config():
    gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY', config.get('OBJECT_STORE_SECRET'))
    gdal.SetConfigOption('AWS_ACCESS_KEY_ID', config.get('OBJECT_STORE_USER_ID'))
    gdal.SetConfigOption('AWS_S3_ENDPOINT', config.get('OBJECT_STORE_SERVER'))
    gdal.SetConfigOption('AWS_VIRTUAL_HOSTING', 'FALSE')

def get_aoi_stats(run_type, for_date, run_datetime, geojson):
    set_gdal_s3_config()
    hfi = get_s3_key(run_type, run_datetime, for_date)
    hfi_raster = gdal.Open(hfi, gdal.GA_ReadOnly)

    geojson_ds = gdal.OpenEx(geojson)

    hfi_prj = hfi_raster.GetProjection()
    hfi_srs = osr.SpatialReference(wkt=hfi_prj)
    layer = geojson_ds.GetLayer()
    srs = layer.GetSpatialRef()

    coordinate_transform = osr.CoordinateTransformation(srs, hfi_srs)

    reprj_geojson =  '/Users/breedwar/projects/aoi_reprojected.gpkg'
    reprojected_ds = ogr.GetDriverByName('GPKG').CreateDataSource(reprj_geojson)
    reprojected_layer = reprojected_ds.CreateLayer('reprojected', srs=hfi_srs)

    # Reproject features and add them to the new data source
    for feature in layer:
        geometry = feature.GetGeometryRef()
        geometry.Transform(coordinate_transform)
        new_feature = ogr.Feature(reprojected_layer.GetLayerDefn())
        new_feature.SetGeometry(geometry)
        reprojected_layer.CreateFeature(new_feature)
        new_feature = None

        area = geometry.GetGeometryRef(0).GetArea()


    warp_options = gdal.WarpOptions(format='GTiff', cutlineDSName=reprj_geojson, cropToCutline=False)
    output = '/Users/breedwar/projects/AOI.tif'
    ds = gdal.Warp(output, hfi_raster, options=warp_options)

    arr = ds.ReadAsArray()
    filt_arr = arr[arr > 0]
    flattened_arr = filt_arr.flatten().tolist()
    
    return flattened_arr, area

