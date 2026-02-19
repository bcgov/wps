"""
FWI processor for calculating FFMC, DMC, DC rasters from weather inputs.

Accepts a FWIInputs dataclass that fully describes the input and output keys,
allowing the same processor to be used for both actuals and forecasts.
"""

import logging
import os
import tempfile
from datetime import datetime
from typing import Callable, Iterator, List, cast

from osgeo import gdal

from wps_shared.geospatial.cog import generate_and_store_cog
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import FWIInputs, FWIParameter
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_sfms.processors.fwi_indices import compute_dc, compute_dmc, compute_ffmc

logger = logging.getLogger(__name__)

MultiDatasetContext = Callable[[List[str]], Iterator[List["WPSDataset"]]]


class FWIProcessor:
    """Calculates FFMC, DMC, DC rasters from weather inputs described by FWIInputs."""

    def __init__(self, datetime_to_process: datetime):
        self.datetime_to_process = datetime_to_process

    async def calculate_ffmc(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        fwi_inputs: FWIInputs,
    ):
        """Calculate FFMC from weather inputs and the previous day's FFMC."""
        await self._calculate_index(s3_client, input_dataset_context, FWIParameter.FFMC, fwi_inputs)

    async def calculate_dmc(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        fwi_inputs: FWIInputs,
    ):
        """Calculate DMC from weather inputs and the previous day's DMC."""
        await self._calculate_index(s3_client, input_dataset_context, FWIParameter.DMC, fwi_inputs)

    async def calculate_dc(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        fwi_inputs: FWIInputs,
    ):
        """Calculate DC from weather inputs and the previous day's DC."""
        await self._calculate_index(s3_client, input_dataset_context, FWIParameter.DC, fwi_inputs)

    async def _calculate_index(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        fwi_param: FWIParameter,
        fwi_inputs: FWIInputs,
    ):
        """
        Calculate a single FWI index from the provided inputs.

        :param s3_client: S3Client instance for checking keys and persisting results
        :param input_dataset_context: Context manager for opening multiple WPSDatasets
        :param fwi_param: Which FWI parameter to calculate (FFMC, DMC, or DC)
        :param fwi_inputs: All S3 keys and metadata for this calculation
        """
        set_s3_gdal_config()

        weather_keys_exist = await s3_client.all_objects_exist(fwi_inputs.temp_key, fwi_inputs.rh_key, fwi_inputs.precip_key)
        if not weather_keys_exist:
            logger.warning("Missing weather keys for %s", self.datetime_to_process.date())
            return

        fwi_key_exists = await s3_client.all_objects_exist(fwi_inputs.prev_fwi_key)
        if not fwi_key_exists:
            logger.warning("Missing previous %s key for %s", fwi_param.value, self.datetime_to_process.date())
            return

        logger.info("Calculating %s %s for %s", fwi_param.value, fwi_inputs.run_type.value, self.datetime_to_process.date())

        with tempfile.TemporaryDirectory() as temp_dir:
            with input_dataset_context([fwi_inputs.temp_key, fwi_inputs.rh_key, fwi_inputs.precip_key, fwi_inputs.prev_fwi_key]) as input_datasets:
                input_datasets = cast(List[WPSDataset], input_datasets)
                temp_ds, rh_ds, precip_ds, prev_fwi_ds = input_datasets

                # Warp weather datasets to match FWI grid
                warped_temp_ds = temp_ds.warp_to_match(
                    prev_fwi_ds, f"{temp_dir}/{os.path.basename(fwi_inputs.temp_key)}.tif", GDALResamplingMethod.BILINEAR
                )
                warped_rh_ds = rh_ds.warp_to_match(
                    prev_fwi_ds, f"{temp_dir}/{os.path.basename(fwi_inputs.rh_key)}.tif", GDALResamplingMethod.BILINEAR, max_value=100
                )
                warped_precip_ds = precip_ds.warp_to_match(
                    prev_fwi_ds, f"{temp_dir}/{os.path.basename(fwi_inputs.precip_key)}.tif", GDALResamplingMethod.BILINEAR
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

                await s3_client.persist_raster_data(
                    temp_dir,
                    fwi_inputs.output_key,
                    prev_fwi_ds.as_gdal_ds().GetGeoTransform(),
                    prev_fwi_ds.as_gdal_ds().GetProjection(),
                    values,
                    nodata_value,
                )

                generate_and_store_cog(src_ds=prev_fwi_ds.as_gdal_ds(), output_path=fwi_inputs.cog_key)
                logger.info("Stored %s %s: %s", fwi_param.value, fwi_inputs.run_type.value, fwi_inputs.output_key)

        gdal.VSICurlClearCache()

