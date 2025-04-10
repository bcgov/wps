from wps_shared import config
from wps_shared.utils.s3 import set_s3_gdal_config


def get_fuel_layer_key():
    """
    Get the latest fuel layer key
    TODO: look up in database
    """
    set_s3_gdal_config()
    bucket = config.get("OBJECT_STORE_BUCKET")
    fuel_raster_name = config.get("FUEL_RASTER_NAME")
    fuel_raster_key = f"/vsis3/{bucket}/sfms/static/{fuel_raster_name}"
    return fuel_raster_key
