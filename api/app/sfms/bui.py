import asyncio
import logging
import os
from tempfile import TemporaryDirectory
from time import perf_counter
from datetime import datetime

import numpy as np
from osgeo import gdal

from app.auto_spatial_advisory.sfms import vectorized_dmc, vectorized_dc
from app.sfms.fwi_input import FWIInput
from app.utils.geospatial import export_to_geotiff, generate_latitude_array
from app.utils.s3 import get_client, set_s3_gdal_config
from app.utils.time import get_utc_now

gdal.UseExceptions()
logger = logging.getLogger(__name__)


def replace_nodata_with_zero(dataset: gdal.Dataset):
    """Reads the first band of a dataset, replaces NoData values with 0, returns the array and the nodata value."""
    band: gdal.Band = dataset.GetRasterBand(1)
    nodata_value = band.GetNoDataValue()
    array = band.ReadAsArray()

    if nodata_value is not None:
        array[array == nodata_value] = 0

    array[(array < 0) & (array > -0.1)] = 0  # TODO remove this once negative precip is fixed

    return array, nodata_value


async def calculate_and_store_dmc(
    datetime_to_calculate_utc: datetime, dmc_ds: gdal.Dataset, temp_ds: gdal.Dataset, rh_ds: gdal.Dataset, precip_ds: gdal.Dataset, latitude: np.ndarray, month: np.ndarray
):
    async with get_client() as (client, bucket):
        key = f"sfms/calculated/forecast/{datetime_to_calculate_utc.date().isoformat()}/dmc{datetime_to_calculate_utc.date().isoformat().replace('-', '')}.tif"

        dmc_array, dmc_nodata_value = replace_nodata_with_zero(dmc_ds)
        temp_array, _ = replace_nodata_with_zero(temp_ds)
        rh_array, _ = replace_nodata_with_zero(rh_ds)
        precip_array, _ = replace_nodata_with_zero(precip_ds)

        start = perf_counter()
        dmc_values = vectorized_dmc(dmc_array, temp_array, rh_array, precip_array, latitude, month, True)
        print(perf_counter() - start)

        if dmc_nodata_value is not None:
            nodata_mask = dmc_ds.GetRasterBand(1).ReadAsArray() == dmc_nodata_value
            dmc_values[nodata_mask] = dmc_nodata_value

        geotransform = dmc_ds.GetGeoTransform()
        projection = dmc_ds.GetProjection()

        logger.info("Uploading dmc to s3")
        with TemporaryDirectory() as temp_dir:
            temp_geotiff = os.path.join(temp_dir, f"dmc{datetime_to_calculate_utc.date().isoformat()}.tif")
            export_to_geotiff(dmc_values, temp_geotiff, geotransform, projection, dmc_nodata_value)

            await client.put_object(Bucket=bucket, Key=key, Body=open(temp_geotiff, "rb"))

        return key


async def calculate_and_store_dc(
    datetime_to_calculate_utc: datetime, dc_ds: gdal.Dataset, temp_ds: gdal.Dataset, rh_ds: gdal.Dataset, precip_ds: gdal.Dataset, latitude: np.ndarray, month: np.ndarray
):
    async with get_client() as (client, bucket):
        key = f"sfms/calculated/forecast/{datetime_to_calculate_utc.date().isoformat()}/dc{datetime_to_calculate_utc.date().isoformat().replace('-', '')}.tif"

        dmc_array, dmc_nodata_value = replace_nodata_with_zero(dc_ds)
        temp_array, _ = replace_nodata_with_zero(temp_ds)
        rh_array, _ = replace_nodata_with_zero(rh_ds)
        precip_array, _ = replace_nodata_with_zero(precip_ds)

        start = perf_counter()
        dmc_values = vectorized_dc(dmc_array, temp_array, rh_array, precip_array, latitude, month, True)
        logger.info("%f seconds to calculate vectorized dc", perf_counter() - start)

        if dmc_nodata_value is not None:
            nodata_mask = dc_ds.GetRasterBand(1).ReadAsArray() == dmc_nodata_value
            dmc_values[nodata_mask] = dmc_nodata_value

        geotransform = dc_ds.GetGeoTransform()
        projection = dc_ds.GetProjection()

        logger.info("Uploading dmc to s3")
        with TemporaryDirectory() as temp_dir:
            temp_geotiff = os.path.join(temp_dir, f"dc{datetime_to_calculate_utc.date().isoformat()}.tif")
            export_to_geotiff(dmc_values, temp_geotiff, geotransform, projection, dmc_nodata_value)

            await client.put_object(Bucket=bucket, Key=key, Body=open(temp_geotiff, "rb"))

        return key


async def calculate_bui():
    set_s3_gdal_config()
    timestamp = get_utc_now()
    # timestamp = datetime(2024, 10, 15, 23, tzinfo=timezone.utc)

    fwi_input = FWIInput(timestamp)
    await fwi_input.check_keys_exist()

    # while fwi_input.s3_keys_exist:
    dmc_ds, dc_ds = fwi_input.open_fwi_datasets()
    transformed_temp, transformed_rh, transformed_precip = fwi_input.warp_weather_to_match_fwi(dmc_ds)

    latitude_array = await generate_latitude_array(fwi_input.dmc_key)
    month_array = np.full(latitude_array.shape, fwi_input.start_time_utc.month)

    dmc_key = await calculate_and_store_dmc(fwi_input.datetime_to_calculate_utc, dmc_ds, transformed_temp, transformed_rh, transformed_precip, latitude_array, month_array)
    dc_key = await calculate_and_store_dc(fwi_input.datetime_to_calculate_utc, dc_ds, transformed_temp, transformed_rh, transformed_precip, latitude_array, month_array)


async def main():
    await calculate_bui()


if __name__ == "__main__":
    asyncio.run(main())
