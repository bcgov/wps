from typing import Optional
from wps_shared import config
from wps_shared.sfms.raster_addresser import RasterKeyAddresser


def get_versioned_fuel_raster_key(
    raster_addresser: RasterKeyAddresser, object_store_path: Optional[str]
):
    """
    Get the latest processed fuel layer key.
    """
    bucket = config.get("OBJECT_STORE_BUCKET")
    if object_store_path is not None:
        return f"/vsis3/{bucket}/{object_store_path}"

    # otherwise default to currently unprocessed fuel raster
    return raster_addresser.get_unprocessed_fuel_raster_key(config.get("FUEL_RASTER_NAME"))
