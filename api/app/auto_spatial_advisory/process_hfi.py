"""Code relating to processing HFI GeoTIFF files, and storing resultant data."""

import logging
import os
from datetime import date, datetime, timedelta
from time import perf_counter
import tempfile
from shapely import wkb, wkt
from shapely.validation import make_valid
from osgeo import ogr, osr
from app.auto_spatial_advisory.common import get_hfi_s3_key
from wps_shared.db.models.auto_spatial_advisory import ClassifiedHfi, HfiClassificationThreshold, RunTypeEnum
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.crud.auto_spatial_advisory import save_hfi, get_hfi_classification_threshold, HfiClassificationThresholdEnum, save_run_parameters, get_run_parameters_id
from wps_shared.db.crud.snow import get_most_recent_processed_snow_by_date
from wps_shared.db.models.snow import SnowSourceEnum
from app.auto_spatial_advisory.classify_hfi import classify_hfi
from wps_shared.run_type import RunType
from app.auto_spatial_advisory.snow import apply_snow_mask
from wps_shared.geospatial.geospatial import NAD83_BC_ALBERS
from app.auto_spatial_advisory.hfi_filepath import get_pmtiles_filename, get_pmtiles_filepath, get_snow_masked_hfi_filepath, get_raster_tif_filename
from wps_shared.utils.polygonize import polygonize_in_memory
from app.utils.pmtiles import tippecanoe_wrapper, write_geojson
from wps_shared.utils.s3 import get_client


logger = logging.getLogger(__name__)

HFI_GEOSPATIAL_PERMISSIONS = "public-read"
HFI_PMTILES_MIN_ZOOM = 4
HFI_PMTILES_MAX_ZOOM = 11


class UnknownHFiClassification(Exception):
    """Raised when the hfi classification is not one of the expected values."""


def get_threshold_from_hfi(feature: ogr.Feature, advisory: HfiClassificationThreshold, warning: HfiClassificationThreshold):
    """
    Parses the HFI id value (1 or 2) attributed to an ogr.Feature, and returns the id of the
    appropriate HfiClassificationThreshold record in the database.
    """
    hfi = feature.GetField(0)
    if hfi == 1:
        return advisory
    elif hfi == 2:
        return warning
    else:
        raise UnknownHFiClassification(f"unknown hfi value: {hfi}")


def create_model_object(
    feature: ogr.Feature,
    advisory: HfiClassificationThreshold,
    warning: HfiClassificationThreshold,
    coordinate_transform: osr.CoordinateTransformation,
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
) -> ClassifiedHfi:
    threshold = get_threshold_from_hfi(feature, advisory, warning)
    # https://gdal.org/api/python/osgeo.ogr.html#osgeo.ogr.Geometry
    geometry: ogr.Geometry = feature.GetGeometryRef()
    # Make sure the geometry is in EPSG:3005!
    geometry.Transform(coordinate_transform)
    # Would be very nice to go directly from the ogr.Geometry into the database,
    # but I can't figure out how to have the wkt output also include the fact that
    # the SRID is EPSG:3005. So we're doing this redundant step of creating a shapely
    # geometry from wkt, then dumping it back into wkb, with srid=3005.
    # NOTE: geometry.ExportToIsoWkb isn't consistent in it's return value between
    # different versions of gdal (bytearray vs. bytestring) - so we're opting for
    # wkt instead of wkb here for better compatibility.
    polygon = wkt.loads(geometry.ExportToIsoWkt())
    polygon = make_valid(polygon)
    return ClassifiedHfi(
        threshold=threshold.id, run_type=RunTypeEnum(run_type.value), run_datetime=run_datetime, for_date=for_date, geom=wkb.dumps(polygon, hex=True, srid=NAD83_BC_ALBERS)
    )


async def process_hfi(run_type: RunType, run_datetime: datetime, for_date: date):
    """Create a new hfi record for the given date.

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_datetime: The date and time of the sfms run in UTC. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """

    # Skip if we already have this run
    async with get_async_read_session_scope() as session:
        existing_run = await get_run_parameters_id(session, run_type, run_datetime, for_date)
        if existing_run is not None:
            logger.info((f"Skipping run, already processed for run_type:{run_type}" f"run_datetime:{run_datetime}," f"for_date:{for_date}"))
            return
        last_processed_snow = await get_most_recent_processed_snow_by_date(session, run_datetime, SnowSourceEnum.viirs)

    logger.info("Processing HFI %s for run date: %s, for date: %s", run_type, run_datetime, for_date)
    perf_start = perf_counter()

    hfi_key = get_hfi_s3_key(run_type, run_datetime, for_date)
    logger.info(f"Key to HFI in object storage: {hfi_key}")
    async with get_client() as (client, bucket):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_filename = os.path.join(temp_dir, "classified.tif")
            classify_hfi(hfi_key, temp_filename)
            # If something has gone wrong with the collection of snow coverage data and it has not been collected
            # within 7 days of the SFMS run datetime, don't apply an old snow mask, work with the classified hfi data as is
            if last_processed_snow is None or last_processed_snow[0].for_date + timedelta(days=7) < run_datetime:
                logger.info("No recently processed snow data found. Proceeding with non-masked hfi data.")
                working_hfi_path = temp_filename
            else:
                # Create a snow coverage mask from previously downloaded snow data.
                working_hfi_path = await apply_snow_mask(temp_filename, last_processed_snow[0], temp_dir)

            raster_filename = get_raster_tif_filename(for_date)
            raster_key = get_snow_masked_hfi_filepath(run_datetime, run_type, raster_filename)
            logger.info(f"Uploading file {raster_filename} to {raster_key}")
            await client.put_object(
                Bucket=bucket,
                Key=raster_key,
                ACL=HFI_GEOSPATIAL_PERMISSIONS,  # We need these to be accessible to everyone
                Body=open(working_hfi_path, "rb"),
            )
            logger.info("Done uploading %s", raster_key)
            with polygonize_in_memory(working_hfi_path, "hfi", "hfi") as layer:
                # We need a geojson file to pass to tippecanoe
                temp_geojson = write_geojson(layer, temp_dir)

                pmtiles_filename = get_pmtiles_filename(for_date)
                temp_pmtiles_filepath = os.path.join(temp_dir, pmtiles_filename)
                logger.info(f"Writing pmtiles -- {pmtiles_filename}")
                tippecanoe_wrapper(temp_geojson, temp_pmtiles_filepath, min_zoom=HFI_PMTILES_MIN_ZOOM, max_zoom=HFI_PMTILES_MAX_ZOOM)

                key = get_pmtiles_filepath(run_datetime, run_type, pmtiles_filename)
                logger.info(f"Uploading file {pmtiles_filename} to {key}")

                await client.put_object(
                    Bucket=bucket,
                    Key=key,
                    ACL=HFI_GEOSPATIAL_PERMISSIONS,  # We need these to be accessible to everyone
                    Body=open(temp_pmtiles_filepath, "rb"),
                )
                logger.info("Done uploading %s", key)

                spatial_reference: osr.SpatialReference = layer.GetSpatialRef()
                target_srs = osr.SpatialReference()
                target_srs.ImportFromEPSG(NAD83_BC_ALBERS)
                target_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
                coordinate_transform = osr.CoordinateTransformation(spatial_reference, target_srs)

                async with get_async_write_session_scope() as session:
                    advisory = await get_hfi_classification_threshold(session, HfiClassificationThresholdEnum.ADVISORY)
                    warning = await get_hfi_classification_threshold(session, HfiClassificationThresholdEnum.WARNING)

                    logger.info("Writing HFI advisory zones to API database...")
                    for i in range(layer.GetFeatureCount()):
                        # https://gdal.org/api/python/osgeo.ogr.html#osgeo.ogr.Feature
                        feature: ogr.Feature = layer.GetFeature(i)
                        obj = create_model_object(feature, advisory, warning, coordinate_transform, run_type, run_datetime, for_date)
                        await save_hfi(session, obj)

                    # Store the unique combination of run type, run datetime and for date in the run_parameters table
                    await save_run_parameters(session, run_type, run_datetime, for_date)

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info("%f delta count before and after processing HFI", delta)
