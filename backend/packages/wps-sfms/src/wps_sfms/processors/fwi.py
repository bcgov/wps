"""
Actual FWI processor for calculating FFMC, DMC, DC from station-interpolated weather.

Uses yesterday's uploaded FWI values as starting inputs and today's interpolated
weather rasters (temperature, relative humidity, precipitation) to calculate
today's actual FFMC, DMC, and DC.
"""

import logging
import os
import tempfile
from datetime import datetime, timedelta
from typing import Callable, Iterator, List, cast

from osgeo import gdal

from wps_shared.geospatial.cog import generate_and_store_cog
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import (
    FWIParameter,
    RasterKeyAddresser,
    SFMSInterpolatedWeatherParameter,
)
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_sfms.processors.fwi_indices import compute_dc, compute_dmc, compute_ffmc

logger = logging.getLogger(__name__)

MultiDatasetContext = Callable[[List[str]], Iterator[List["WPSDataset"]]]


class ActualFWIProcessor:
    """Calculates FFMC, DMC, DC rasters from interpolated weather + yesterday's FWI."""

    def __init__(self, datetime_to_process: datetime, raster_addresser: RasterKeyAddresser):
        self.datetime_to_process = datetime_to_process
        self.raster_addresser = raster_addresser

    async def calculate_ffmc(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
    ):
        """Calculate today's FFMC from interpolated weather and yesterday's FFMC."""
        await self._calculate_index(s3_client, input_dataset_context, FWIParameter.FFMC)

    async def calculate_dmc(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
    ):
        """Calculate today's DMC from interpolated weather and yesterday's DMC."""
        await self._calculate_index(s3_client, input_dataset_context, FWIParameter.DMC)

    async def calculate_dc(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
    ):
        """Calculate today's DC from interpolated weather and yesterday's DC."""
        await self._calculate_index(s3_client, input_dataset_context, FWIParameter.DC)

    async def _calculate_index(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        fwi_param: FWIParameter,
    ):
        """
        Calculate a single FWI index from interpolated weather and yesterday's value.

        :param s3_client: S3Client instance for checking keys and persisting results
        :param input_dataset_context: Context manager for opening multiple WPSDatasets
        :param fwi_param: Which FWI parameter to calculate (FFMC, DMC, or DC)
        """
        set_s3_gdal_config()

        yesterday = self.datetime_to_process - timedelta(days=1)

        # Build S3 keys for today's interpolated weather
        temp_key = self.raster_addresser.get_interpolated_key(
            self.datetime_to_process, SFMSInterpolatedWeatherParameter.TEMP
        )
        rh_key = self.raster_addresser.get_interpolated_key(
            self.datetime_to_process, SFMSInterpolatedWeatherParameter.RH
        )
        precip_key = self.raster_addresser.get_interpolated_key(
            self.datetime_to_process, SFMSInterpolatedWeatherParameter.PRECIP
        )

        # Build S3 key for yesterday's FWI value
        prev_fwi_key = self.raster_addresser.get_uploaded_index_key(yesterday, fwi_param)

        # Check all input keys exist
        weather_keys_exist = await s3_client.all_objects_exist(temp_key, rh_key, precip_key)
        if not weather_keys_exist:
            logger.warning("Missing interpolated weather keys for %s", self.datetime_to_process.date())
            return

        fwi_key_exists = await s3_client.all_objects_exist(prev_fwi_key)
        if not fwi_key_exists:
            logger.warning("Missing previous %s key for %s", fwi_param.value, yesterday.date())
            return

        logger.info("Calculating %s actual for %s", fwi_param.value, self.datetime_to_process.date())

        # Prefix keys for GDAL access
        temp_key, rh_key, precip_key, prev_fwi_key = self.raster_addresser.gdal_prefix_keys(
            temp_key, rh_key, precip_key, prev_fwi_key
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with input_dataset_context([temp_key, rh_key, precip_key, prev_fwi_key]) as input_datasets:
                input_datasets = cast(List[WPSDataset], input_datasets)
                temp_ds, rh_ds, precip_ds, prev_fwi_ds = input_datasets

                # Warp weather datasets to match FWI grid
                warped_temp_ds = temp_ds.warp_to_match(
                    prev_fwi_ds, f"{temp_dir}/{os.path.basename(temp_key)}.tif", GDALResamplingMethod.BILINEAR
                )
                warped_rh_ds = rh_ds.warp_to_match(
                    prev_fwi_ds, f"{temp_dir}/{os.path.basename(rh_key)}.tif", GDALResamplingMethod.BILINEAR, max_value=100
                )
                warped_precip_ds = precip_ds.warp_to_match(
                    prev_fwi_ds, f"{temp_dir}/{os.path.basename(precip_key)}.tif", GDALResamplingMethod.BILINEAR
                )

                # Close raw weather datasets to free memory
                temp_ds.close()
                rh_ds.close()
                precip_ds.close()

                # Compute the index
                compute_fns = {
                    FWIParameter.FFMC: lambda: compute_ffmc(prev_fwi_ds, warped_temp_ds, warped_rh_ds, warped_precip_ds),
                    FWIParameter.DMC: lambda: compute_dmc(prev_fwi_ds, warped_temp_ds, warped_rh_ds, warped_precip_ds, self.datetime_to_process.month),
                    FWIParameter.DC: lambda: compute_dc(prev_fwi_ds, warped_temp_ds, warped_rh_ds, warped_precip_ds, self.datetime_to_process.month),
                }
                values, nodata_value = compute_fns[fwi_param]()

                # Persist result to S3
                output_key = self.raster_addresser.get_calculated_index_key(
                    self.datetime_to_process, fwi_param, run_type="actual"
                )
                cog_key = self.raster_addresser.get_cog_key(output_key)

                await s3_client.persist_raster_data(
                    temp_dir,
                    output_key,
                    prev_fwi_ds.as_gdal_ds().GetGeoTransform(),
                    prev_fwi_ds.as_gdal_ds().GetProjection(),
                    values,
                    nodata_value,
                )

                generate_and_store_cog(src_ds=prev_fwi_ds.as_gdal_ds(), output_path=cog_key)
                logger.info("Stored %s actual: %s", fwi_param.value, output_key)

        gdal.VSICurlClearCache()
