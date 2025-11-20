import os
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import numpy
import tempfile
from osgeo import gdal
from wps_shared import config
from numba import vectorize
from wps_shared.utils.s3 import get_client, read_into_memory
from wps_shared.weather_models import ModelEnum
from wps_shared.sfms.rdps_filename_marshaller import adjust_forecast_hour, compose_rdps_key, compose_computed_precip_rdps_key

logger = logging.getLogger(__name__)

RDPS_PRECIP_ACC_RASTER_PERMISSIONS = "public-read"


@dataclass
class TemporalPrecip:
    """Precip values at certain times"""

    timestamp: str
    precip_amount: float | numpy.ndarray

    def is_after(self, other) -> bool:
        return self.timestamp > other.timestamp


async def compute_and_store_precip_rasters(model_run_timestamp: datetime):
    """
    Given a UTC datetime, trigger 36 hours worth of accumulated precip
    difference rasters and store them.
    """
    async with get_client() as (client, bucket):
        for hour in range(0, 36):
            accumulation_timestamp = model_run_timestamp + timedelta(hours=hour)
            (precip_diff_raster, geotransform, projection) = await generate_24_hour_accumulating_precip_raster(accumulation_timestamp)
            if precip_diff_raster is None:
                # If there is no precip_diff_raster, RDPS precip data is not available. We'll retry the cron job in one hour.
                logger.warning(f"No precip raster data for hour: {hour} and model run timestamp: {model_run_timestamp.strftime('%Y-%m-%d_%H:%M:%S')}")
                break
            key = f"weather_models/{ModelEnum.RDPS.lower()}/{accumulation_timestamp.date().isoformat()}/" + compose_computed_precip_rdps_key(
                accumulation_end_datetime=accumulation_timestamp
            )

            res = await client.list_objects_v2(Bucket=bucket, Prefix=key, MaxKeys=1)
            if "Contents" in res:
                logger.info("File already exists for key: %s, skipping", key)
                continue

            bucket = config.get("OBJECT_STORE_BUCKET")

            logger.info(
                "Uploading RDPS 24 hour acc precip raster for date: %s, hour: %s, forecast hour: %s to %s",
                model_run_timestamp.date().isoformat(),
                model_run_timestamp.hour,
                adjust_forecast_hour(model_run_timestamp.hour, hour),
                key,
            )
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_filename = os.path.join(temp_dir, model_run_timestamp.date().isoformat() + "precip" + str(hour) + ".tif")
                # Create temp file
                driver = gdal.GetDriverByName("GTiff")
                rows, cols = precip_diff_raster.shape
                output_dataset = driver.Create(temp_filename, cols, rows, 1, gdal.GDT_Float32)
                output_dataset.SetGeoTransform(geotransform)
                output_dataset.SetProjection(projection)

                if output_dataset is None:
                    raise IOError("Unable to create %s", key)

                output_band = output_dataset.GetRasterBand(1)
                output_band.WriteArray(precip_diff_raster)
                output_band.FlushCache()
                output_dataset = None
                del output_dataset
                output_band = None
                del output_band

                await client.put_object(
                    Bucket=bucket,
                    Key=key,
                    ACL=RDPS_PRECIP_ACC_RASTER_PERMISSIONS,  # We need these to be accessible to everyone
                    Body=open(temp_filename, "rb"),
                )

                logger.info("Done uploading file to %s", key)


async def generate_24_hour_accumulating_precip_raster(timestamp: datetime):
    """
    Given a UTC datetime, grab the raster for that date
    and the date for 24 hours before to compute the difference.
    """
    (yesterday_key, today_key) = get_raster_keys_to_diff(timestamp)
    (day_data, day_geotransform, day_projection) = await read_into_memory(today_key)
    if day_data is None:
        return (day_data, day_geotransform, day_projection)
    if yesterday_key is None:
        return (day_data, day_geotransform, day_projection)

    yesterday_time = timestamp - timedelta(days=1)
    (yesterday_data, _, _) = await read_into_memory(yesterday_key)
    if yesterday_data is None:
        raise ValueError("No precip raster data for yesterday_key: %s" % yesterday_key)

    later_precip = TemporalPrecip(timestamp=timestamp, precip_amount=day_data)
    earlier_precip = TemporalPrecip(timestamp=yesterday_time, precip_amount=yesterday_data)
    return (compute_precip_difference(later_precip, earlier_precip), day_geotransform, day_projection)


def get_raster_keys_to_diff(timestamp: datetime):
    """
    To maintain the invariant that only the same model runs are diffed, we need to grab the latest
    model run that has data greater than 24 hours ago, but less than 36 hours ago.
    """
    target_model_run_date = timestamp - timedelta(hours=24)
    key_prefix = f"weather_models/{ModelEnum.RDPS.lower()}/{target_model_run_date.date().isoformat()}"
    # From earlier model run, get the keys for 24 hours before timestamp and the timestamp to perform the diff
    earlier_key = f"{key_prefix}/"
    later_key = f"{key_prefix}/"
    later_key = later_key + compose_rdps_key(target_model_run_date, target_model_run_date.hour, target_model_run_date.hour + 24, "precip")
    if target_model_run_date.hour != 0 and target_model_run_date.hour != 12:
        # not a model run hour, return earlier and later keys to take difference
        earlier_key = earlier_key + compose_rdps_key(target_model_run_date, target_model_run_date.hour, target_model_run_date.hour, "precip")
        return (earlier_key, later_key)

    # model run hour, just return the model value from 24 hours ago
    return (None, later_key)


def compute_precip_difference(later_precip: TemporalPrecip, earlier_precip: TemporalPrecip):
    """
    Simple function to compute difference between later and earlier precip values
    to be vectorized with numba.
    """
    if not later_precip.is_after(earlier_precip):
        raise ValueError("Later precip value must be after earlier precip value")
    return vectorized_diff(later_precip.precip_amount, earlier_precip.precip_amount)


def _diff(value_a: float, value_b: float):
    """
    Subtract value_a from value_b.
    :param value_a: The first value
    :param value_b: The second value
    :raises ValueError: If difference is less than -0.01 (ie. negative precip not allowed)
    :return: Return value_a minus value_b if the value is >= 0. If the difference is slightly negative (-0.01 <= value < 0), due to floating
    point math for example, return 0. If the value is truly negative, raise an error.
    """
    result = value_a - value_b
    if result < -0.01:
        raise ValueError("Precip difference cannot be negative")
    return result if result > 0 else 0


vectorized_diff = vectorize(_diff)
