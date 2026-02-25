"""
FWI processor for calculating FFMC, DMC, DC rasters from weather inputs.

Accepts a FWIInputs dataclass that fully describes the input and output keys,
allowing the same processor to be used for both actuals and forecasts.
"""

import logging
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable, Iterator, List, Tuple, cast

import numpy as np
from osgeo import gdal

from wps_shared.geospatial.cog import generate_and_store_cog
from wps_shared.geospatial.geospatial import rasters_match
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import FWIInputs, FWIParameter
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_sfms.processors.fwi_indices import compute_dc, compute_dmc, compute_ffmc

logger = logging.getLogger(__name__)

MultiDatasetContext = Callable[[List[str]], Iterator[List["WPSDataset"]]]


class FWICalculator(ABC):
    fwi_param: FWIParameter

    @abstractmethod
    def calculate(self, prev_fwi_ds: WPSDataset, temp_ds: WPSDataset, rh_ds: WPSDataset, precip_ds: WPSDataset) -> Tuple[np.ndarray, float]:
        ...


class FFMCCalculator(FWICalculator):
    fwi_param = FWIParameter.FFMC

    def calculate(self, prev_fwi_ds, temp_ds, rh_ds, precip_ds):
        return compute_ffmc(prev_fwi_ds, temp_ds, rh_ds, precip_ds)


class DMCCalculator(FWICalculator):
    fwi_param = FWIParameter.DMC

    def __init__(self, month: int):
        self.month = month

    def calculate(self, prev_fwi_ds, temp_ds, rh_ds, precip_ds):
        return compute_dmc(prev_fwi_ds, temp_ds, rh_ds, precip_ds, self.month)


class DCCalculator(FWICalculator):
    fwi_param = FWIParameter.DC

    def __init__(self, month: int):
        self.month = month

    def calculate(self, prev_fwi_ds, temp_ds, rh_ds, precip_ds):
        return compute_dc(prev_fwi_ds, temp_ds, rh_ds, precip_ds, self.month)


class FWIProcessor:
    """Calculates FFMC, DMC, DC rasters from weather inputs described by FWIInputs."""

    def __init__(self, datetime_to_process: datetime):
        self.datetime_to_process = datetime_to_process

    async def calculate_index(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        calculator: FWICalculator,
        fwi_inputs: FWIInputs,
    ):
        """
        Calculate a single FWI index from the provided inputs.

        :param s3_client: S3Client instance for checking keys and persisting results
        :param input_dataset_context: Context manager for opening multiple WPSDatasets
        :param calculator: FWICalculator instance that performs the index calculation
        :param fwi_inputs: All S3 keys and metadata for this calculation
        """
        set_s3_gdal_config()

        weather_keys_exist = await s3_client.all_objects_exist(
            fwi_inputs.temp_key, fwi_inputs.rh_key, fwi_inputs.precip_key
        )
        if not weather_keys_exist:
            logger.warning("Missing weather keys for %s", self.datetime_to_process.date())
            return

        fwi_key_exists = await s3_client.all_objects_exist(fwi_inputs.prev_fwi_key)
        if not fwi_key_exists:
            logger.warning(
                "Missing previous %s key for %s", calculator.fwi_param.value, self.datetime_to_process.date()
            )
            return

        logger.info(
            "Calculating %s %s for %s",
            calculator.fwi_param.value,
            fwi_inputs.run_type.value,
            self.datetime_to_process.date(),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with input_dataset_context(
                [
                    fwi_inputs.temp_key,
                    fwi_inputs.rh_key,
                    fwi_inputs.precip_key,
                    fwi_inputs.prev_fwi_key,
                ]
            ) as input_datasets:
                input_datasets = cast(List[WPSDataset], input_datasets)
                temp_ds, rh_ds, precip_ds, prev_fwi_ds = input_datasets

                # Assert weather rasters already match the FWI grid
                if not rasters_match(temp_ds.as_gdal_ds(), prev_fwi_ds.as_gdal_ds()):
                    raise ValueError("Temperature raster does not match FWI grid")
                if not rasters_match(rh_ds.as_gdal_ds(), prev_fwi_ds.as_gdal_ds()):
                    raise ValueError("RH raster does not match FWI grid")
                if not rasters_match(precip_ds.as_gdal_ds(), prev_fwi_ds.as_gdal_ds()):
                    raise ValueError("Precip raster does not match FWI grid")

                values, nodata_value = calculator.calculate(prev_fwi_ds, temp_ds, rh_ds, precip_ds)

                await s3_client.persist_raster_data(
                    temp_dir,
                    fwi_inputs.output_key,
                    prev_fwi_ds.as_gdal_ds().GetGeoTransform(),
                    prev_fwi_ds.as_gdal_ds().GetProjection(),
                    values,
                    nodata_value,
                )

                generate_and_store_cog(
                    src_ds=prev_fwi_ds.as_gdal_ds(), output_path=fwi_inputs.cog_key
                )
                logger.info(
                    "Stored %s %s: %s",
                    calculator.fwi_param.value,
                    fwi_inputs.run_type.value,
                    fwi_inputs.output_key,
                )

                # Clear gdal virtual file system cache of S3 metadata
                gdal.VSICurlClearCache()
