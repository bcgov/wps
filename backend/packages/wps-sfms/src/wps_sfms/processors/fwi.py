"""
FWI processor for calculating FFMC, DMC, DC rasters from weather inputs.

Accepts a FWIInputs dataclass that fully describes the input and output keys,
allowing the same processor to be used for both actuals and forecasts.
"""

import logging
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from time import perf_counter
from typing import Callable, ContextManager, List, NamedTuple, Tuple, cast

import numpy as np
from osgeo import gdal

from wps_shared.fwi import vectorized_dc, vectorized_dmc, vectorized_ffmc
from wps_shared.geospatial.cog import generate_and_store_cog
from wps_shared.geospatial.geospatial import rasters_match
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import FWIParameter
from wps_sfms.sfmsng_raster_addresser import FWIInputs
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client

logger = logging.getLogger(__name__)

MultiDatasetContext = Callable[[List[str]], ContextManager[List["WPSDataset"]]]


class FWIResult(NamedTuple):
    values: np.ndarray
    nodata_value: float


class FWICalculator(ABC):
    fwi_param: FWIParameter

    @abstractmethod
    def calculate(
        self, prev_fwi_ds: WPSDataset, temp_ds: WPSDataset, rh_ds: WPSDataset, precip_ds: WPSDataset
    ) -> FWIResult: ...


class MonthlyFWICalculator(FWICalculator, ABC):
    """Base for indices that require latitude and month arrays (DMC, DC)."""

    def __init__(self, month: int):
        if not 1 <= month <= 12:
            raise ValueError(f"month must be 1–12, got {month}")
        self.month = month

    def _lat_month_arrays(self, ds: WPSDataset) -> Tuple[np.ndarray, np.ndarray]:
        latitude = ds.generate_latitude_array()
        return latitude, np.full(latitude.shape, self.month)


class FFMCCalculator(FWICalculator):
    fwi_param = FWIParameter.FFMC

    def calculate(
        self, prev_fwi_ds: WPSDataset, temp_ds: WPSDataset, rh_ds: WPSDataset, precip_ds: WPSDataset
    ) -> FWIResult:
        ffmc_yda, nodata_value = prev_fwi_ds.replace_nodata_with(np.nan)
        temp, _ = temp_ds.replace_nodata_with(np.nan)
        rh, _ = rh_ds.replace_nodata_with(np.nan)
        prec, _ = precip_ds.replace_nodata_with(np.nan)
        ws = np.zeros_like(temp)  # TODO: implement wind speed

        mask = np.isnan(ffmc_yda) | np.isnan(temp) | np.isnan(rh) | np.isnan(prec)
        valid = ~mask
        values = np.full(ffmc_yda.shape, nodata_value, dtype=ffmc_yda.dtype)

        start = perf_counter()
        values[valid] = vectorized_ffmc(ffmc_yda[valid], temp[valid], rh[valid], ws[valid], prec[valid])
        logger.info("%f seconds to calculate vectorized ffmc", perf_counter() - start)

        return FWIResult(values, nodata_value)


class DMCCalculator(MonthlyFWICalculator):
    fwi_param = FWIParameter.DMC

    def calculate(
        self, prev_fwi_ds: WPSDataset, temp_ds: WPSDataset, rh_ds: WPSDataset, precip_ds: WPSDataset
    ) -> FWIResult:
        lat, mon = self._lat_month_arrays(prev_fwi_ds)
        dmc_yda, nodata_value = prev_fwi_ds.replace_nodata_with(np.nan)
        temp, _ = temp_ds.replace_nodata_with(np.nan)
        rh, _ = rh_ds.replace_nodata_with(np.nan)
        prec, _ = precip_ds.replace_nodata_with(np.nan)

        mask = np.isnan(dmc_yda) | np.isnan(temp) | np.isnan(rh) | np.isnan(prec)
        valid = ~mask
        values = np.full(dmc_yda.shape, nodata_value, dtype=dmc_yda.dtype)

        start = perf_counter()
        values[valid] = vectorized_dmc(dmc_yda[valid], temp[valid], rh[valid], prec[valid], lat[valid], mon[valid], True)
        logger.info("%f seconds to calculate vectorized dmc", perf_counter() - start)

        return FWIResult(values, nodata_value)


class DCCalculator(MonthlyFWICalculator):
    fwi_param = FWIParameter.DC

    def calculate(
        self, prev_fwi_ds: WPSDataset, temp_ds: WPSDataset, rh_ds: WPSDataset, precip_ds: WPSDataset
    ) -> FWIResult:
        lat, mon = self._lat_month_arrays(prev_fwi_ds)
        dc_yda, nodata_value = prev_fwi_ds.replace_nodata_with(np.nan)
        temp, _ = temp_ds.replace_nodata_with(np.nan)
        rh, _ = rh_ds.replace_nodata_with(np.nan)
        prec, _ = precip_ds.replace_nodata_with(np.nan)

        mask = np.isnan(dc_yda) | np.isnan(temp) | np.isnan(rh) | np.isnan(prec)
        valid = ~mask
        values = np.full(dc_yda.shape, nodata_value, dtype=dc_yda.dtype)

        start = perf_counter()
        values[valid] = vectorized_dc(dc_yda[valid], temp[valid], rh[valid], prec[valid], lat[valid], mon[valid], True)
        logger.info("%f seconds to calculate vectorized dc", perf_counter() - start)

        return FWIResult(values, nodata_value)


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
            raise RuntimeError(
                f"Missing weather keys for {self.datetime_to_process.date()}: "
                f"temp={fwi_inputs.temp_key}, rh={fwi_inputs.rh_key}, precip={fwi_inputs.precip_key}"
            )

        fwi_key_exists = await s3_client.all_objects_exist(fwi_inputs.prev_fwi_key)
        if not fwi_key_exists:
            raise RuntimeError(
                f"Missing previous {calculator.fwi_param.value} raster for "
                f"{self.datetime_to_process.date()}: {fwi_inputs.prev_fwi_key}"
            )

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
                    raise ValueError(
                        f"Temperature raster does not match FWI grid: {fwi_inputs.temp_key} vs {fwi_inputs.prev_fwi_key}"
                    )
                if not rasters_match(rh_ds.as_gdal_ds(), prev_fwi_ds.as_gdal_ds()):
                    raise ValueError(
                        f"RH raster does not match FWI grid: {fwi_inputs.rh_key} vs {fwi_inputs.prev_fwi_key}"
                    )
                if not rasters_match(precip_ds.as_gdal_ds(), prev_fwi_ds.as_gdal_ds()):
                    raise ValueError(
                        f"Precip raster does not match FWI grid: {fwi_inputs.precip_key} vs {fwi_inputs.prev_fwi_key}"
                    )

                result = calculator.calculate(prev_fwi_ds, temp_ds, rh_ds, precip_ds)

                await s3_client.persist_raster_data(
                    temp_dir,
                    fwi_inputs.output_key,
                    prev_fwi_ds.as_gdal_ds().GetGeoTransform(),
                    prev_fwi_ds.as_gdal_ds().GetProjection(),
                    result.values,
                    result.nodata_value,
                )

                with WPSDataset.from_array(
                    result.values,
                    prev_fwi_ds.as_gdal_ds().GetGeoTransform(),
                    prev_fwi_ds.as_gdal_ds().GetProjection(),
                    result.nodata_value,
                ) as output_ds:
                    generate_and_store_cog(src_ds=output_ds.as_gdal_ds(), output_path=fwi_inputs.cog_key)
                logger.info(
                    "Stored %s %s: %s",
                    calculator.fwi_param.value,
                    fwi_inputs.run_type.value,
                    fwi_inputs.output_key,
                )

                # Clear gdal virtual file system cache of S3 metadata
                gdal.VSICurlClearCache()
