"""Build daily temporal fuel grids from the BC base fuel grid and Julian-date season rasters.

The temporal grid translates BC base fuel values to national FBP fuel lookup values, then
applies green-up so leafless deciduous and mixedwood fuels become their green variants on
dates inside each pixel's green-up period.
"""

import logging
from datetime import date

import numpy as np
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.schemas.sfms import FuelCodesLookup
from wps_shared.sfms.raster_addresser import GDALPath, S3Key
from wps_shared.utils.s3 import gdal_s3_context
from wps_shared.utils.s3_client import S3Client

from wps_sfms.fbp_fuel_types import (
    GREEN_UP_GRID_VALUES,
    NATIONAL_FUEL_LOOKUP,
    NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE,
)
from wps_sfms.publish import publish_dataset
from wps_sfms.raster_dependencies import GriddedRasterDependencies

logger = logging.getLogger(__name__)


def calculate_temporal_fuel(
    base_fuel: np.ndarray,
    green_up_on: np.ndarray,
    green_up_off: np.ndarray,
    target_date: date,
) -> np.ndarray:
    """Return national fuel grid values for ``target_date``, with NaN where the base is nodata.

    A pixel is green when ``green_up_on <= day of year < green_up_off``. Missing Julian values
    (NaN) never green up. A ``ValueError`` is raised for unrecognized base fuel values.
    """
    temporal = np.full(base_fuel.shape, np.nan, dtype=np.float32)
    for bc_value, national_value in NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE.items():
        temporal[base_fuel == bc_value] = national_value

    unrecognized = np.isfinite(base_fuel) & np.isnan(temporal)
    if np.any(unrecognized):
        values = sorted(np.unique(base_fuel[unrecognized]).tolist())
        raise ValueError(f"Base fuel raster contains unsupported classifications: {values}")

    day_of_year = target_date.timetuple().tm_yday
    green = (green_up_on <= day_of_year) & (day_of_year < green_up_off)
    for leafless_value, green_value in GREEN_UP_GRID_VALUES.items():
        temporal[green & (temporal == leafless_value)] = green_value
    return temporal


def fuel_codes_lookup(temporal: np.ndarray) -> FuelCodesLookup:
    """Return the national fuel lookup rows for the grid values present in ``temporal``."""
    grid_values = np.unique(temporal[np.isfinite(temporal)]).astype(int).tolist()
    return FuelCodesLookup([NATIONAL_FUEL_LOOKUP[value] for value in grid_values])


async def publish_temporal_fuel_raster(
    s3_client: S3Client,
    base_fuel_key: GDALPath,
    green_up_on_key: GDALPath,
    green_up_off_key: GDALPath,
    target_date: date,
    output_key: S3Key,
    fuel_codes_lookup_path: S3Key,
) -> str:
    """Calculate, store and return the content hash of the temporal fuel raster for one date.

    The raster keeps the base grid's geometry, data type and nodata value. Its COG uses
    nearest-neighbour resampling so fuel classifications are not blended.
    """
    dependencies = GriddedRasterDependencies()
    with gdal_s3_context():
        await dependencies.assert_keys_exist(
            s3_client, (base_fuel_key, green_up_on_key, green_up_off_key)
        )
        with (
            WPSDataset(base_fuel_key) as base_fuel,
            WPSDataset(green_up_on_key) as green_up_on,
            WPSDataset(green_up_off_key) as green_up_off,
        ):
            dependencies.validate_grids(
                base_fuel, {"green_up_on": green_up_on, "green_up_off": green_up_off}
            )
            base_values, _ = base_fuel.replace_nodata_with(np.nan)
            on_values, _ = green_up_on.replace_nodata_with(np.nan)
            off_values, _ = green_up_off.replace_nodata_with(np.nan)
            temporal = calculate_temporal_fuel(base_values, on_values, off_values, target_date)

            nodata_value = base_fuel.require_nodata_value()
            band = base_fuel.as_gdal_ds().GetRasterBand(1)
            with WPSDataset.from_array(
                np.where(np.isnan(temporal), nodata_value, temporal),
                base_fuel,
                nodata_value,
                datatype=band.DataType,
            ) as output_ds:
                output_ds.as_gdal_ds().GetRasterBand(1).SetDescription("fbp_fuel_type")
                published = await publish_dataset(
                    s3_client,
                    output_ds,
                    output_key,
                    cog_resample_alg=GDALResamplingMethod.NEAREST_NEIGHBOUR,
                )

    await s3_client.put_object(
        key=fuel_codes_lookup_path, body=fuel_codes_lookup(temporal).model_dump_json().encode()
    )
    logger.info(
        "Stored temporal fuel raster for %s: %s (COG: %s, fuel codes lookup: %s)",
        target_date,
        published.output_key,
        published.cog_key,
        fuel_codes_lookup_path,
    )
    return await s3_client.get_content_hash(output_key)
