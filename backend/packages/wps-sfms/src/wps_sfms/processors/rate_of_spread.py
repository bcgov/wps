"""Raster processor for Fire Behaviour Prediction rate of spread."""

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Generator

import numpy as np
from cffdrs_vec.fbp import vectorized_rate_of_spread
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import GDALPath
from wps_shared.utils.s3 import gdal_s3_context
from wps_shared.utils.s3_client import S3Client

from wps_sfms.fbp_fuel_types import (
    NODATA_FUEL_TYPE_CODE,
    NON_COMBUSTIBLE_FUEL_VALUES,
    fuel_type_codes_from_grid,
)
from wps_sfms.fbp_input_validation import validate_percent_conifer
from wps_sfms.interpolation.common import SFMS_NO_DATA
from wps_sfms.publish import publish_dataset
from wps_sfms.raster_dependencies import GriddedRasterDependencies, MultiDatasetContext
from wps_sfms.raster_inputs import RateOfSpreadInputs
from wps_sfms.raster_output import create_masked_output_dataset, open_bc_mask_dataset

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateOfSpreadResult:
    values: np.ndarray
    nodata_value: float = SFMS_NO_DATA


@dataclass(frozen=True)
class RateOfSpreadDatasets:
    fuel: WPSDataset
    isi: WPSDataset
    bui: WPSDataset
    fmc: WPSDataset
    sfc: WPSDataset
    percent_conifer: WPSDataset


def calculate_rate_of_spread(datasets: RateOfSpreadDatasets) -> RateOfSpreadResult:
    """Calculate ROS using the same mixedwood validation rules as SFC."""
    fuel, _ = datasets.fuel.replace_nodata_with(np.nan)
    isi, _ = datasets.isi.replace_nodata_with(np.nan)
    bui, _ = datasets.bui.replace_nodata_with(np.nan)
    fmc, _ = datasets.fmc.replace_nodata_with(np.nan)
    sfc, _ = datasets.sfc.replace_nodata_with(np.nan)
    percent_conifer, _ = datasets.percent_conifer.replace_nodata_with(np.nan)

    fuel_type_codes = fuel_type_codes_from_grid(fuel)
    validate_percent_conifer(fuel, percent_conifer)

    non_combustible_mask = np.isin(fuel, tuple(NON_COMBUSTIBLE_FUEL_VALUES))
    calculation_mask = (
        ~non_combustible_mask
        & (fuel_type_codes != NODATA_FUEL_TYPE_CODE)
        & np.isfinite(isi)
        & np.isfinite(bui)
        & np.isfinite(fmc)
        & np.isfinite(sfc)
    )

    output = np.full(fuel.shape, SFMS_NO_DATA, dtype=np.float32)
    if np.any(calculation_mask):
        start = perf_counter()
        pdf = np.zeros_like(isi[calculation_mask], dtype=np.float32)
        cc = np.zeros_like(isi[calculation_mask], dtype=np.float32)
        cbh = np.zeros_like(isi[calculation_mask], dtype=np.float32)
        calculated = vectorized_rate_of_spread(
            fuel_type_codes[calculation_mask],
            isi[calculation_mask],
            bui[calculation_mask],
            fmc[calculation_mask],
            sfc[calculation_mask],
            percent_conifer[calculation_mask],
            pdf,
            cc,
            cbh,
        )
        logger.info("%f seconds to calculate vectorized ROS", perf_counter() - start)
        output[calculation_mask] = np.where(np.isfinite(calculated), calculated, SFMS_NO_DATA)

    output[non_combustible_mask] = 0
    return RateOfSpreadResult(output)


class RateOfSpreadProcessor:
    """Load, validate, calculate, and publish one daily ROS raster."""

    def __init__(self, datetime_to_process: datetime):
        self.datetime_to_process = datetime_to_process
        self._raster_dependencies = GriddedRasterDependencies()

    @staticmethod
    def _dependency_keys(inputs: RateOfSpreadInputs) -> tuple[GDALPath, ...]:
        return (
            inputs.fuel_key,
            inputs.isi_key,
            inputs.bui_key,
            inputs.fmc_key,
            inputs.sfc_key,
            inputs.percent_conifer_key,
        )

    @contextmanager
    def _open_datasets(
        self,
        input_dataset_context: MultiDatasetContext,
        inputs: RateOfSpreadInputs,
    ) -> Generator[RateOfSpreadDatasets, None, None]:
        with self._raster_dependencies.open_by_key(
            input_dataset_context, self._dependency_keys(inputs)
        ) as datasets_by_key:
            yield RateOfSpreadDatasets(
                fuel=datasets_by_key[inputs.fuel_key],
                isi=datasets_by_key[inputs.isi_key],
                bui=datasets_by_key[inputs.bui_key],
                fmc=datasets_by_key[inputs.fmc_key],
                sfc=datasets_by_key[inputs.sfc_key],
                percent_conifer=datasets_by_key[inputs.percent_conifer_key],
            )

    def _validate_grids(self, datasets: RateOfSpreadDatasets) -> None:
        self._raster_dependencies.validate_grids(
            datasets.fuel,
            {
                "isi": datasets.isi,
                "bui": datasets.bui,
                "fmc": datasets.fmc,
                "sfc": datasets.sfc,
                "percent_conifer": datasets.percent_conifer,
            },
        )

    async def process(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        inputs: RateOfSpreadInputs,
    ) -> None:
        """Calculate and publish ROS from the declared raster dependencies."""
        with gdal_s3_context():
            await self._raster_dependencies.assert_keys_exist(
                s3_client,
                self._dependency_keys(inputs),
            )
            logger.info(
                "Calculating ROS %s for %s",
                inputs.run_type.value,
                self.datetime_to_process.date(),
            )

            with self._open_datasets(input_dataset_context, inputs) as datasets:
                self._validate_grids(datasets)
                result = calculate_rate_of_spread(datasets)

                with (
                    open_bc_mask_dataset() as mask,
                    create_masked_output_dataset(
                        result.values,
                        datasets.fuel,
                        mask,
                        result.nodata_value,
                    ) as output_ds,
                ):
                    output_band = output_ds.as_gdal_ds().GetRasterBand(1)
                    output_band.SetDescription("rate_of_spread")
                    output_band.SetUnitType("m/min")
                    published = await publish_dataset(
                        s3_client=s3_client,
                        dataset=output_ds,
                        output_key=inputs.output_key,
                    )

            logger.info(
                "Stored ROS %s: %s (COG: %s)",
                inputs.run_type.value,
                published.output_key,
                published.cog_key,
            )
