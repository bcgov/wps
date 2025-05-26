from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared import config
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.db.crud.fuel_layer import get_most_recent_fuel_layer
from wps_shared.sfms.raster_addresser import RasterKeyAddresser


async def get_latest_fuel_raster_key(
    session: AsyncSession, raster_addresser: RasterKeyAddresser, year: int, version: int
):
    """
    Get the latest processed fuel layer key
    """
    set_s3_gdal_config()
    bucket = config.get("OBJECT_STORE_BUCKET")
    latest_processed_fuel_raster: Optional[FuelTypeRaster] = await get_most_recent_fuel_layer(
        session
    )
    if latest_processed_fuel_raster is not None:
        return f"/vsis3/{bucket}/{latest_processed_fuel_raster.object_store_path}"

    # otherwise default to currently unprocessed fuel raster
    return raster_addresser.get_unprocessed_fuel_raster_key(config.get("FUEL_RASTER_NAME"))
