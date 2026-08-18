"""Raster processor for Fire Behaviour Prediction surface fuel consumption."""

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Callable, ContextManager, Generator, List

import numpy as np
from cffdrs_vec.fbp import vectorized_surface_fuel_consumption
from wps_shared.geospatial.geospatial import rasters_match
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.utils.s3 import gdal_s3_context
from wps_shared.utils.s3_client import S3Client

from wps_sfms.fbp_fuel_types import (
    GRASS_FUEL_LOAD,
    NODATA_FUEL_TYPE_CODE,
    NON_COMBUSTIBLE_FUEL_VALUES,
    PERCENT_CONIFER_GRID_VALUES,
    fuel_type_codes_from_grid,
)
from wps_sfms.interpolation.common import SFMS_NO_DATA
from wps_sfms.publish import publish_dataset
from wps_sfms.raster_inputs import SurfaceFuelConsumptionInputs
from wps_sfms.raster_output import create_masked_output_dataset

logger = logging.getLogger(__name__)

MultiDatasetContext = Callable[[List[str]], ContextManager[List[WPSDataset]]]


@dataclass(frozen=True)
class SurfaceFuelConsumptionResult:
    values: np.ndarray
    nodata_value: float = SFMS_NO_DATA


@dataclass(frozen=True)
class SurfaceFuelConsumptionDatasets:
    fuel: WPSDataset
    ffmc: WPSDataset
    bui: WPSDataset
    percent_conifer: WPSDataset


def _prepare_percent_conifer(fuel: np.ndarray, percent_conifer: np.ndarray) -> np.ndarray:
    mixedwood_mask = np.isin(fuel, tuple(PERCENT_CONIFER_GRID_VALUES))
    invalid = mixedwood_mask & (
        ~np.isfinite(percent_conifer) | (percent_conifer < 0) | (percent_conifer > 100)
    )
    if np.any(invalid):
        raise ValueError(
            "Percent-conifer raster contains missing or out-of-range values on mixedwood pixels"
        )

    calculation_values = np.zeros(fuel.shape, dtype=np.float64)
    calculation_values[mixedwood_mask] = percent_conifer[mixedwood_mask]
    return calculation_values


def calculate_surface_fuel_consumption(
    datasets: SurfaceFuelConsumptionDatasets,
) -> SurfaceFuelConsumptionResult:
    """Calculate SFC with zero for recognized non-fuel pixels."""
    fuel, _ = datasets.fuel.replace_nodata_with(np.nan)
    ffmc, _ = datasets.ffmc.replace_nodata_with(np.nan)
    bui, _ = datasets.bui.replace_nodata_with(np.nan)
    percent_conifer, _ = datasets.percent_conifer.replace_nodata_with(np.nan)

    fuel_type_codes = fuel_type_codes_from_grid(fuel)
    calculation_percent_conifer = _prepare_percent_conifer(fuel, percent_conifer)

    non_combustible_mask = np.isin(fuel, tuple(NON_COMBUSTIBLE_FUEL_VALUES))
    calculation_mask = (
        ~non_combustible_mask
        & (fuel_type_codes != NODATA_FUEL_TYPE_CODE)
        & np.isfinite(ffmc)
        & np.isfinite(bui)
    )
    output = np.full(fuel.shape, SFMS_NO_DATA, dtype=np.float32)
    if np.any(calculation_mask):
        start = perf_counter()
        calculated = vectorized_surface_fuel_consumption(
            fuel_type_codes[calculation_mask],
            ffmc[calculation_mask],
            bui[calculation_mask],
            calculation_percent_conifer[calculation_mask],
            GRASS_FUEL_LOAD,
        )
        logger.info("%f seconds to calculate vectorized SFC", perf_counter() - start)
        output[calculation_mask] = np.where(np.isfinite(calculated), calculated, SFMS_NO_DATA)

    # cffdrs clamps to a 0.000001 floor, so set recognized non-fuel pixels to exact zero.
    output[non_combustible_mask] = 0
    return SurfaceFuelConsumptionResult(output)


class SurfaceFuelConsumptionProcessor:
    """Load, validate, calculate, and publish one daily SFC raster."""

    def __init__(self, datetime_to_process: datetime):
        self.datetime_to_process = datetime_to_process

    async def _assert_dependencies_exist(
        self, s3_client: S3Client, inputs: SurfaceFuelConsumptionInputs
    ) -> None:
        dependency_keys = (
            inputs.fuel_key,
            inputs.ffmc_key,
            inputs.bui_key,
            inputs.percent_conifer_key,
        )
        if not await s3_client.all_objects_exist(*dependency_keys):
            details = ", ".join(str(key) for key in dependency_keys)
            raise RuntimeError(
                f"Missing SFC dependencies for {self.datetime_to_process.date()}: {details}"
            )

    @contextmanager
    def _open_datasets(
        self,
        input_dataset_context: MultiDatasetContext,
        inputs: SurfaceFuelConsumptionInputs,
    ) -> Generator[SurfaceFuelConsumptionDatasets, None, None]:
        keys = [
            inputs.fuel_key,
            inputs.ffmc_key,
            inputs.bui_key,
            inputs.percent_conifer_key,
        ]
        with input_dataset_context(keys) as input_datasets:
            datasets_by_key = {dataset.ds_path: dataset for dataset in input_datasets}
            yield SurfaceFuelConsumptionDatasets(
                fuel=datasets_by_key[inputs.fuel_key],
                ffmc=datasets_by_key[inputs.ffmc_key],
                bui=datasets_by_key[inputs.bui_key],
                percent_conifer=datasets_by_key[inputs.percent_conifer_key],
            )

    @staticmethod
    def _validate_grids(
        datasets: SurfaceFuelConsumptionDatasets, inputs: SurfaceFuelConsumptionInputs
    ) -> None:
        reference = datasets.fuel.as_gdal_ds()
        candidates = (
            ("ffmc", inputs.ffmc_key, datasets.ffmc),
            ("bui", inputs.bui_key, datasets.bui),
            ("percent_conifer", inputs.percent_conifer_key, datasets.percent_conifer),
        )
        for label, key, dataset in candidates:
            if not rasters_match(dataset.as_gdal_ds(), reference):
                raise ValueError(
                    f"{label} raster does not match the fuel grid: {key} vs {inputs.fuel_key}"
                )

    async def process(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        inputs: SurfaceFuelConsumptionInputs,
    ) -> None:
        """Calculate and publish SFC from the declared raster dependencies."""
        with gdal_s3_context():
            await self._assert_dependencies_exist(s3_client, inputs)
            logger.info(
                "Calculating SFC %s for %s",
                inputs.run_type.value,
                self.datetime_to_process.date(),
            )

            with self._open_datasets(input_dataset_context, inputs) as datasets:
                self._validate_grids(datasets, inputs)
                result = calculate_surface_fuel_consumption(datasets)

                with create_masked_output_dataset(
                    result.values,
                    datasets.fuel,
                    result.nodata_value,
                ) as output_ds:
                    output_band = output_ds.as_gdal_ds().GetRasterBand(1)
                    output_band.SetDescription("surface_fuel_consumption")
                    output_band.SetUnitType("kg/m2")
                    published = await publish_dataset(
                        s3_client=s3_client,
                        dataset=output_ds,
                        output_key=inputs.output_key,
                    )

            logger.info(
                "Stored SFC %s: %s (COG: %s)",
                inputs.run_type.value,
                published.output_key,
                published.cog_key,
            )
