"""The temporal fuel stage of an SFMS run."""

import logging

from botocore.exceptions import ClientError
from wps_shared.db.crud.fuel_layer import (
    get_latest_temporal_fuel_raster_version,
    get_matching_temporal_fuel_raster,
    lock_temporal_fuel_raster_date,
)
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.db.models.temporal_fuel_raster import TemporalFuelRaster
from wps_shared.sfms.raster_addresser import GDALPath
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now

from wps_sfms.julian_rasters import ensure_julian_archives, read_julian_rasters
from wps_sfms.processors.temporal_fuel import publish_temporal_fuel_raster
from wps_sfms.run_context import SFMSRunContext

logger = logging.getLogger(__name__)


async def resolve_temporal_fuel(context: SFMSRunContext) -> GDALPath:
    """Resolve the date's temporal fuel raster from the base fuel grid and Julian rasters,
    creating a new version when needed, and return its path.

    An existing raster is reused only when it was built from the same base fuel raster and the
    same green-up and grass curing Julian date rasters, and the stored raster still matches its
    recorded hash. The Julian rasters are recorded by archive key, since the live Julian keys are
    replaced over time.
    """
    target_date = context.datetime_to_process.date()
    fuel_type_raster = context.fuel_type_raster
    raster_addresser = context.raster_addresser
    s3_client = context.s3_client

    async def _resolve() -> GDALPath:
        julian = await read_julian_rasters(s3_client, raster_addresser)
        # outside the date lock: concurrent runs would write identical bytes to the same keys
        await ensure_julian_archives(s3_client, julian)
        context.manifest.record_julian_rasters(
            {raster.name: raster.archive_key for raster in julian}
        )

        async with get_async_write_session_scope() as session:
            # held until commit so concurrent runs for the same date reuse rather than collide
            await lock_temporal_fuel_raster_date(session, target_date)
            existing = await get_matching_temporal_fuel_raster(
                session, target_date, fuel_type_raster.id, **julian.hash_columns()
            )
            if existing is not None and await _stored_raster_matches(s3_client, existing):
                logger.info(
                    "Reusing temporal fuel raster for %s: %s",
                    target_date,
                    existing.object_store_path,
                )
                return raster_addresser.gdal_path(existing.object_store_path)
            # a grid is fully determined by its inputs, so a missing or altered one is rebuilt as
            # the next version, which the reuse query then prefers

            version = await get_latest_temporal_fuel_raster_version(session, target_date) + 1
            output_key = raster_addresser.get_temporal_fuel_key(target_date, version)
            logger.info(
                "Generating temporal fuel raster for %s, version %s, base raster %s: %s",
                target_date,
                version,
                fuel_type_raster.id,
                output_key,
            )
            with julian.as_datasets() as julian_datasets:
                content_hash = await publish_temporal_fuel_raster(
                    s3_client,
                    target_date,
                    base_fuel_key=context.base_fuel_raster_path,
                    output_key=output_key,
                    julian=julian_datasets,
                )
            session.add(
                TemporalFuelRaster(
                    fuel_type_raster_id=fuel_type_raster.id,
                    for_date=target_date,
                    version=version,
                    object_store_path=output_key,
                    content_hash=content_hash,
                    **julian.hash_columns(),
                    **julian.archive_path_columns(),
                    create_timestamp=get_utc_now(),
                )
            )
        return raster_addresser.gdal_path(output_key)

    temporal_fuel_path = await context.track(SFMSRunLogJobName.TEMPORAL_FUEL, _resolve)
    context.manifest.record_temporal_fuel_raster(temporal_fuel_path)
    return temporal_fuel_path


async def _stored_raster_matches(s3_client: S3Client, existing: TemporalFuelRaster) -> bool:
    """Return whether the stored raster still exists and matches its recorded content hash."""
    try:
        await s3_client.get_fuel_raster(existing.object_store_path, existing.content_hash)
    except ValueError:
        logger.warning(
            "Stored temporal fuel raster no longer matches its recorded hash: %s",
            existing.object_store_path,
        )
        return False
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("404", "NoSuchKey"):
            raise
        logger.warning("Stored temporal fuel raster is missing: %s", existing.object_store_path)
        return False
    return True
