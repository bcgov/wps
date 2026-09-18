"""Fire-zone raster validation shared by advisory processing entry points."""

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.crud.auto_spatial_advisory import (
    get_advisory_shape_ids_by_source_identifier,
)
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.zonal_stats import iter_raster_windows
from wps_shared.sfms.raster_addresser import BaseRasterAddresser
from wps_shared.utils.s3 import gdal_s3_context


async def validate_fire_zone_raster(session: AsyncSession) -> None:
    """Validate the static zone raster once before running the advisory processors.

    Cells other than the declared nodata value are source identifiers that must map to
    advisory-shape rows. Keeping this check at the pipeline boundary avoids rescanning the zone IDs
    in every processing step.
    """
    raster_source_identifiers: set[int] = set()
    zone_path = BaseRasterAddresser().get_fire_zone_units_path()
    with gdal_s3_context(), WPSDataset(zone_path) as zones:
        zone_nodata = zones.require_nodata_value()
        for window in iter_raster_windows([zones.ds]):
            (zone_ids,) = window.arrays
            raster_source_identifiers.update(
                int(zone_id) for zone_id in np.unique(zone_ids[zone_ids != zone_nodata])
            )

    source_to_shape_id = await get_advisory_shape_ids_by_source_identifier(session)
    unknown = raster_source_identifiers - source_to_shape_id.keys()
    if unknown:
        raise ValueError(f"Fire-zone raster contains unknown source identifiers: {sorted(unknown)}")
