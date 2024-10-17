import asyncio
import os
from tempfile import TemporaryDirectory
from datetime import datetime, timedelta
from osgeo import gdal
import numpy as np
from aiobotocore.client import AioBaseClient

from app.sfms.raster_addresser import FWIParameter, RasterKeyAddresser, WeatherParameter
from app.sfms.raster_processor import calculate_dmc, calculate_dc
from app.utils.geospatial import export_to_geotiff, generate_latitude_array, warp_to_match
from app.utils.s3 import all_objects_exist, get_client, set_s3_gdal_config
from app.utils.time import get_utc_now


class DateRangeProcessor:
    """
    Encapsulates logic for iterating over a date range and performing some unit of work.
    TODO: either make specific to BUI or generalize it better.
    """

    def __init__(self, start_datetime: datetime, days: int):
        self.start_datetime = start_datetime
        self.days = days

    async def process_bui(self):
        raster_addresser = RasterKeyAddresser()
        set_s3_gdal_config()

        async with get_client() as (client, bucket):
            for day in range(self.days):
                datetime_to_calculate_utc = self.start_datetime.replace(hour=20, minute=0, second=0, microsecond=0) + timedelta(days=day)
                previous_fwi_datetime = datetime_to_calculate_utc - timedelta(days=1)
                prediction_hour = 20 + (day * 24)

                temp_key, rh_key, _, precip_key = raster_addresser.get_weather_data_keys(self.start_datetime, datetime_to_calculate_utc, prediction_hour)

                weather_keys_exist = await all_objects_exist(temp_key, rh_key, precip_key)

                if not weather_keys_exist:
                    break

                dc_key = raster_addresser.get_calculated_index_key(previous_fwi_datetime, FWIParameter.DC)
                dmc_key = raster_addresser.get_calculated_index_key(previous_fwi_datetime, FWIParameter.DMC)

                fwi_keys_exist = await all_objects_exist(dc_key, dmc_key)

                if not fwi_keys_exist:
                    dc_key = raster_addresser.get_uploaded_index_key(self.start_datetime, FWIParameter.DC)
                    dmc_key = raster_addresser.get_uploaded_index_key(self.start_datetime, FWIParameter.DMC)

                    fwi_keys_exist = await all_objects_exist(dc_key, dmc_key)

                    if not fwi_keys_exist:
                        break

                temp_key, rh_key, precip_key = raster_addresser.gdal_prefix_keys(temp_key, rh_key, precip_key)
                dc_key, dmc_key = raster_addresser.gdal_prefix_keys(dc_key, dmc_key)

                temp_ds: gdal.Dataset = gdal.Open(temp_key)
                rh_ds: gdal.Dataset = gdal.Open(rh_key)
                precip_ds: gdal.Dataset = gdal.Open(precip_key)

                dc_ds: gdal.Dataset = gdal.Open(dc_key)
                dmc_ds: gdal.Dataset = gdal.Open(dmc_key)

                warped_temp_ds = warp_to_match(WeatherParameter.TEMP.value, temp_ds, dmc_ds)
                warped_rh_ds = warp_to_match(WeatherParameter.RH.value, rh_ds, dmc_ds)
                warped_precip_ds = warp_to_match("precip", precip_ds, dmc_ds)

                temp_ds = None
                rh_ds = None
                precip_ds = None

                latitude_array = generate_latitude_array(dmc_ds)
                month_array = np.full(latitude_array.shape, datetime_to_calculate_utc.month)

                dmc_values, dmc_nodata_value = calculate_dmc(dmc_ds, warped_temp_ds, warped_rh_ds, warped_precip_ds, latitude_array, month_array)
                dc_values, dc_nodata_value = calculate_dc(dc_ds, warped_temp_ds, warped_rh_ds, warped_precip_ds, latitude_array, month_array)

                new_dmc_key = raster_addresser.get_calculated_index_key(datetime_to_calculate_utc, FWIParameter.DMC)
                await self.store_raster(
                    client, bucket, new_dmc_key, FWIParameter.DMC, datetime_to_calculate_utc, dmc_ds.GetGeoTransform(), dmc_ds.GetProjection(), dmc_values, dmc_nodata_value
                )

                new_dc_key = raster_addresser.get_calculated_index_key(datetime_to_calculate_utc, FWIParameter.DC)
                await self.store_raster(
                    client, bucket, new_dc_key, FWIParameter.DC, datetime_to_calculate_utc, dc_ds.GetGeoTransform(), dc_ds.GetProjection(), dc_values, dc_nodata_value
                )

                dmc_ds = None
                dc_ds = None

    async def store_raster(
        self, client: AioBaseClient, bucket: str, key: str, fwi_param: FWIParameter, datetime_to_calculate_utc: datetime, transform, projection, values, no_data_value
    ):
        with TemporaryDirectory() as temp_dir:
            temp_geotiff = os.path.join(temp_dir, f"{fwi_param.value}{datetime_to_calculate_utc.date().isoformat()}.tif")
            export_to_geotiff(values, temp_geotiff, transform, projection, no_data_value)

            await client.put_object(Bucket=bucket, Key=key, Body=open(temp_geotiff, "rb"))


async def main():
    start_time = get_utc_now()
    days = 2

    processor = DateRangeProcessor(start_time, days)
    await processor.process_bui()


if __name__ == "__main__":
    asyncio.run(main())
