"""
FWI processor for calculating FWI index rasters from weather/index dependencies.

Accepts an FWIInputs dataclass that declares all dependency keys and output keys,
allowing each calculator to specify only the inputs it needs.
"""

from dataclasses import dataclass
import logging
import tempfile
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from time import perf_counter
from typing import Callable, ContextManager, Iterator, List, Mapping, NamedTuple

import numpy as np
from osgeo import gdal

from wps_shared.fwi import (
    vectorized_bui,
    vectorized_dc,
    vectorized_dmc,
    vectorized_ffmc,
    vectorized_fwi,
    vectorized_isi,
)
from wps_shared.geospatial.cog import generate_and_store_cog
from wps_shared.geospatial.geospatial import rasters_match
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import FWIParameter, SFMSInterpolatedWeatherParameter
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_sfms.sfmsng_raster_addresser import FWIInputs

logger = logging.getLogger(__name__)

MultiDatasetContext = Callable[[List[str]], ContextManager[List["WPSDataset"]]]
WeatherDatasetMap = dict[SFMSInterpolatedWeatherParameter, WPSDataset]
IndexDatasetMap = dict[FWIParameter, WPSDataset]


@dataclass
class FWIDatasets:
    index: IndexDatasetMap
    weather: WeatherDatasetMap


class FWIResult(NamedTuple):
    values: np.ndarray
    nodata_value: float


class FWICalculator(ABC):
    fwi_param: FWIParameter
    reference_index_param: FWIParameter
    required_weather_params: tuple[SFMSInterpolatedWeatherParameter, ...] = ()
    required_index_params: tuple[FWIParameter, ...] = ()

    @abstractmethod
    def calculate(self, datasets: FWIDatasets) -> FWIResult: ...


class MonthlyFWICalculator(FWICalculator, ABC):
    """Base for indices that require latitude and month arrays (DMC, DC)."""

    def __init__(self, month: int):
        if not 1 <= month <= 12:
            raise ValueError(f"month must be 1–12, got {month}")
        self.month = month

    def _lat_month_arrays(self, ds: WPSDataset) -> tuple[np.ndarray, np.ndarray]:
        latitude = ds.generate_latitude_array()
        return latitude, np.full(latitude.shape, self.month)


class FFMCCalculator(FWICalculator):
    fwi_param = FWIParameter.FFMC
    reference_index_param = FWIParameter.FFMC
    required_weather_params = (
        SFMSInterpolatedWeatherParameter.TEMP,
        SFMSInterpolatedWeatherParameter.RH,
        SFMSInterpolatedWeatherParameter.PRECIP,
        SFMSInterpolatedWeatherParameter.WIND_SPEED,
    )
    required_index_params = (FWIParameter.FFMC,)

    def calculate(self, datasets: FWIDatasets) -> FWIResult:
        temp_ds = datasets.weather[SFMSInterpolatedWeatherParameter.TEMP]
        rh_ds = datasets.weather[SFMSInterpolatedWeatherParameter.RH]
        precip_ds = datasets.weather[SFMSInterpolatedWeatherParameter.PRECIP]
        wind_ds = datasets.weather[SFMSInterpolatedWeatherParameter.WIND_SPEED]
        ffmc_prev_ds = datasets.index[FWIParameter.FFMC]

        ffmc_prev, nodata_value = ffmc_prev_ds.replace_nodata_with(np.nan)
        temp, _ = temp_ds.replace_nodata_with(np.nan)
        rh, _ = rh_ds.replace_nodata_with(np.nan)
        prec, _ = precip_ds.replace_nodata_with(np.nan)
        ws, _ = wind_ds.replace_nodata_with(np.nan)

        mask = np.isnan(ffmc_prev) | np.isnan(temp) | np.isnan(rh) | np.isnan(prec) | np.isnan(ws)
        valid = ~mask
        values = np.full(ffmc_prev.shape, nodata_value, dtype=ffmc_prev.dtype)

        start = perf_counter()
        values[valid] = vectorized_ffmc(
            ffmc_prev[valid], temp[valid], rh[valid], ws[valid], prec[valid]
        )
        logger.info("%f seconds to calculate vectorized ffmc", perf_counter() - start)

        return FWIResult(values, nodata_value)


class DMCCalculator(MonthlyFWICalculator):
    fwi_param = FWIParameter.DMC
    reference_index_param = FWIParameter.DMC
    required_weather_params = (
        SFMSInterpolatedWeatherParameter.TEMP,
        SFMSInterpolatedWeatherParameter.RH,
        SFMSInterpolatedWeatherParameter.PRECIP,
    )
    required_index_params = (FWIParameter.DMC,)

    def calculate(self, datasets: FWIDatasets) -> FWIResult:
        temp_ds = datasets.weather[SFMSInterpolatedWeatherParameter.TEMP]
        rh_ds = datasets.weather[SFMSInterpolatedWeatherParameter.RH]
        precip_ds = datasets.weather[SFMSInterpolatedWeatherParameter.PRECIP]
        dmc_prev_ds = datasets.index[FWIParameter.DMC]

        lat, mon = self._lat_month_arrays(dmc_prev_ds)
        dmc_prev, nodata_value = dmc_prev_ds.replace_nodata_with(np.nan)
        temp, _ = temp_ds.replace_nodata_with(np.nan)
        rh, _ = rh_ds.replace_nodata_with(np.nan)
        prec, _ = precip_ds.replace_nodata_with(np.nan)

        mask = np.isnan(dmc_prev) | np.isnan(temp) | np.isnan(rh) | np.isnan(prec)
        valid = ~mask
        values = np.full(dmc_prev.shape, nodata_value, dtype=dmc_prev.dtype)

        start = perf_counter()
        values[valid] = vectorized_dmc(
            dmc_prev[valid], temp[valid], rh[valid], prec[valid], lat[valid], mon[valid], True
        )
        logger.info("%f seconds to calculate vectorized dmc", perf_counter() - start)

        return FWIResult(values, nodata_value)


class DCCalculator(MonthlyFWICalculator):
    fwi_param = FWIParameter.DC
    reference_index_param = FWIParameter.DC
    required_weather_params = (
        SFMSInterpolatedWeatherParameter.TEMP,
        SFMSInterpolatedWeatherParameter.RH,
        SFMSInterpolatedWeatherParameter.PRECIP,
    )
    required_index_params = (FWIParameter.DC,)

    def calculate(self, datasets: FWIDatasets) -> FWIResult:
        temp_ds = datasets.weather[SFMSInterpolatedWeatherParameter.TEMP]
        rh_ds = datasets.weather[SFMSInterpolatedWeatherParameter.RH]
        precip_ds = datasets.weather[SFMSInterpolatedWeatherParameter.PRECIP]
        dc_prev_ds = datasets.index[FWIParameter.DC]

        lat, mon = self._lat_month_arrays(dc_prev_ds)
        dc_prev, nodata_value = dc_prev_ds.replace_nodata_with(np.nan)
        temp, _ = temp_ds.replace_nodata_with(np.nan)
        rh, _ = rh_ds.replace_nodata_with(np.nan)
        prec, _ = precip_ds.replace_nodata_with(np.nan)

        mask = np.isnan(dc_prev) | np.isnan(temp) | np.isnan(rh) | np.isnan(prec)
        valid = ~mask
        values = np.full(dc_prev.shape, nodata_value, dtype=dc_prev.dtype)

        start = perf_counter()
        values[valid] = vectorized_dc(
            dc_prev[valid], temp[valid], rh[valid], prec[valid], lat[valid], mon[valid], True
        )
        logger.info("%f seconds to calculate vectorized dc", perf_counter() - start)

        return FWIResult(values, nodata_value)


class ISICalculator(FWICalculator):
    fwi_param = FWIParameter.ISI
    reference_index_param = FWIParameter.FFMC
    required_weather_params = (SFMSInterpolatedWeatherParameter.WIND_SPEED,)
    required_index_params = (FWIParameter.FFMC,)

    def calculate(self, datasets: FWIDatasets) -> FWIResult:
        ffmc_ds = datasets.index[FWIParameter.FFMC]
        wind_ds = datasets.weather[SFMSInterpolatedWeatherParameter.WIND_SPEED]

        ffmc, nodata_value = ffmc_ds.replace_nodata_with(np.nan)
        ws, _ = wind_ds.replace_nodata_with(np.nan)

        mask = np.isnan(ffmc) | np.isnan(ws)
        valid = ~mask
        values = np.full(ffmc.shape, nodata_value, dtype=ffmc.dtype)

        start = perf_counter()
        values[valid] = vectorized_isi(ffmc[valid], ws[valid], False)
        logger.info("%f seconds to calculate vectorized isi", perf_counter() - start)

        return FWIResult(values, nodata_value)


class BUICalculator(FWICalculator):
    fwi_param = FWIParameter.BUI
    reference_index_param = FWIParameter.DMC
    required_index_params = (FWIParameter.DMC, FWIParameter.DC)

    def calculate(self, datasets: FWIDatasets) -> FWIResult:
        dmc_ds = datasets.index[FWIParameter.DMC]
        dc_ds = datasets.index[FWIParameter.DC]

        dmc, nodata_value = dmc_ds.replace_nodata_with(np.nan)
        dc, _ = dc_ds.replace_nodata_with(np.nan)

        mask = np.isnan(dmc) | np.isnan(dc)
        valid = ~mask
        values = np.full(dmc.shape, nodata_value, dtype=dmc.dtype)

        start = perf_counter()
        values[valid] = vectorized_bui(dmc[valid], dc[valid])
        logger.info("%f seconds to calculate vectorized bui", perf_counter() - start)

        return FWIResult(values, nodata_value)


class FWIFinalCalculator(FWICalculator):
    fwi_param = FWIParameter.FWI
    reference_index_param = FWIParameter.ISI
    required_index_params = (FWIParameter.ISI, FWIParameter.BUI)

    def calculate(self, datasets: FWIDatasets) -> FWIResult:
        isi_ds = datasets.index[FWIParameter.ISI]
        bui_ds = datasets.index[FWIParameter.BUI]

        isi, nodata_value = isi_ds.replace_nodata_with(np.nan)
        bui, _ = bui_ds.replace_nodata_with(np.nan)

        mask = np.isnan(isi) | np.isnan(bui)
        valid = ~mask
        values = np.full(isi.shape, nodata_value, dtype=isi.dtype)

        start = perf_counter()
        values[valid] = vectorized_fwi(isi[valid], bui[valid])
        logger.info("%f seconds to calculate vectorized fwi", perf_counter() - start)

        return FWIResult(values, nodata_value)


class FWIProcessor:
    """Calculates FWI index rasters from dependency keys described by FWIInputs."""

    def __init__(self, datetime_to_process: datetime):
        self.datetime_to_process = datetime_to_process

    @staticmethod
    def _get_required_weather_keys(
        calculator: FWICalculator,
        fwi_inputs: FWIInputs,
    ) -> dict[SFMSInterpolatedWeatherParameter, str]:
        missing_params = [
            param
            for param in calculator.required_weather_params
            if param not in fwi_inputs.weather_keys
        ]
        if missing_params:
            missing = ", ".join(param.value for param in missing_params)
            raise ValueError(f"FWIInputs missing weather key mappings for: {missing}")

        return {
            param: fwi_inputs.weather_keys[param] for param in calculator.required_weather_params
        }

    @staticmethod
    def _get_required_index_keys(
        calculator: FWICalculator,
        fwi_inputs: FWIInputs,
    ) -> dict[FWIParameter, str]:
        missing_params = [
            param
            for param in calculator.required_index_params
            if param not in fwi_inputs.index_keys
        ]
        if missing_params:
            missing = ", ".join(param.value for param in missing_params)
            raise ValueError(f"FWIInputs missing index key mappings for: {missing}")

        return {param: fwi_inputs.index_keys[param] for param in calculator.required_index_params}

    async def _assert_dependency_keys_exist(
        self,
        s3_client: S3Client,
        keys_by_param: Mapping[SFMSInterpolatedWeatherParameter | FWIParameter, str],
        dependency_kind: str,
    ) -> None:
        if not keys_by_param:
            return

        if await s3_client.all_objects_exist(*keys_by_param.values()):
            return

        details = ", ".join(f"{param.value}={key}" for param, key in keys_by_param.items())
        raise RuntimeError(
            f"Missing {dependency_kind} keys for {self.datetime_to_process.date()}: {details}"
        )

    @contextmanager
    def _open_required_datasets(
        self,
        input_dataset_context: MultiDatasetContext,
        weather_keys_by_param: Mapping[SFMSInterpolatedWeatherParameter, str],
        index_keys_by_param: Mapping[FWIParameter, str],
    ) -> Iterator[FWIDatasets]:
        """
        Open all required weather/index dependency rasters and yield them as `FWIDatasets`.

        This method opens every key in one context manager and reorganizes the resulting
        datasets back into parameter-keyed weather and index maps for calculator consumption.
        """
        input_keys = [*weather_keys_by_param.values(), *index_keys_by_param.values()]
        with input_dataset_context(input_keys) as input_datasets:
            datasets_by_key: dict[str, WPSDataset] = {}
            for ds in input_datasets:
                datasets_by_key[ds.ds_path] = ds

            weather_datasets: WeatherDatasetMap = {
                param: datasets_by_key[key] for param, key in weather_keys_by_param.items()
            }
            index_datasets: IndexDatasetMap = {
                param: datasets_by_key[key] for param, key in index_keys_by_param.items()
            }

            yield FWIDatasets(index=index_datasets, weather=weather_datasets)

    async def calculate_index(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        calculator: FWICalculator,
        fwi_inputs: FWIInputs,
    ):
        """
        Calculate a single FWI index from the provided dependencies.

        :param s3_client: S3Client instance for checking keys and persisting results
        :param input_dataset_context: Context manager for opening dependency datasets
        :param calculator: FWICalculator instance that performs the index calculation
        :param fwi_inputs: Dependency keys and metadata for this calculation
        """
        set_s3_gdal_config()

        # get only the dependency keys required by this calculator.
        # ex: ISI uses FFMC + wind speed, while BUI uses DMC + DC.
        weather_keys_by_param = self._get_required_weather_keys(calculator, fwi_inputs)
        index_keys_by_param = self._get_required_index_keys(calculator, fwi_inputs)

        await self._assert_dependency_keys_exist(
            s3_client, weather_keys_by_param, "weather dependency"
        )
        await self._assert_dependency_keys_exist(s3_client, index_keys_by_param, "index dependency")

        logger.info(
            "Calculating %s %s for %s",
            calculator.fwi_param.value,
            fwi_inputs.run_type.value,
            self.datetime_to_process.date(),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with self._open_required_datasets(
                input_dataset_context, weather_keys_by_param, index_keys_by_param
            ) as datasets:
                weather_datasets = datasets.weather
                index_datasets = datasets.index

                # use reference index's geotransform and projection for the output dataset, and verify all dependencies match that grid
                reference_ds = index_datasets[calculator.reference_index_param]
                reference_key = index_keys_by_param[calculator.reference_index_param]

                # every weather raster must match the reference index grid
                for param in calculator.required_weather_params:
                    weather_ds = weather_datasets[param]
                    weather_key = weather_keys_by_param[param]
                    if not rasters_match(weather_ds.as_gdal_ds(), reference_ds.as_gdal_ds()):
                        raise ValueError(
                            f"{param.value} raster does not match FWI grid: {weather_key} vs {reference_key}"
                        )

                # every index raster must match the reference index grid
                for param in calculator.required_index_params:
                    if param == calculator.reference_index_param:
                        continue
                    index_ds = index_datasets[param]
                    index_key = index_keys_by_param[param]
                    if not rasters_match(index_ds.as_gdal_ds(), reference_ds.as_gdal_ds()):
                        raise ValueError(
                            f"{param.value} raster does not match FWI grid: {index_key} vs {reference_key}"
                        )

                result = calculator.calculate(datasets)

                # store GeoTIFF output using georeferencing from the reference grid
                await s3_client.persist_raster_data(
                    temp_dir,
                    fwi_inputs.output_key,
                    reference_ds.as_gdal_ds().GetGeoTransform(),
                    reference_ds.as_gdal_ds().GetProjection(),
                    result.values,
                    result.nodata_value,
                )

                # generate/store a COG from the computed raster array
                with WPSDataset.from_array(
                    result.values,
                    reference_ds.as_gdal_ds().GetGeoTransform(),
                    reference_ds.as_gdal_ds().GetProjection(),
                    result.nodata_value,
                ) as output_ds:
                    generate_and_store_cog(
                        src_ds=output_ds.as_gdal_ds(), output_path=fwi_inputs.cog_key
                    )

                logger.info(
                    "Stored %s %s: %s",
                    calculator.fwi_param.value,
                    fwi_inputs.run_type.value,
                    fwi_inputs.output_key,
                )

                # Clear gdal virtual file system cache of S3 metadata.
                gdal.VSICurlClearCache()
