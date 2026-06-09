from typing import Optional
from wps_shared import config


def get_versioned_fuel_raster_key(object_store_path: Optional[str]):
    """
    Get the GDAL path for a processed fuel layer key.
    """
    bucket = config.get("OBJECT_STORE_BUCKET")
    if object_store_path is not None:
        return f"/vsis3/{bucket}/{object_store_path}"

    raise ValueError("A processed fuel raster object_store_path is required.")
