"""Raster processor for the shared primary Fire Behaviour Prediction calculation."""

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Generator

import numpy as np
from cffdrs_vec.fbp import vectorized_primary_fire_behaviour_prediction
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
from wps_sfms.raster_inputs import PrimaryFireBehaviourInputs
from wps_sfms.raster_output import create_masked_output_dataset, open_bc_mask_dataset

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PrimaryFireBehaviourResult:
    values: np.ndarray
    nodata_value: float = SFMS_NO_DATA


@dataclass(frozen=True)
class PrimaryFireBehaviourDatasets:
    fuel: WPSDataset
    ffmc: WPSDataset
    bui: WPSDataset
    wind_speed: WPSDataset
    wind_direction: WPSDataset
    slope: WPSDataset | None
    aspect: WPSDataset | None
    percent_conifer: WPSDataset
    fmc: WPSDataset
    isi: WPSDataset


def calculate_primary_fire_behaviour(
    datasets: PrimaryFireBehaviourDatasets,
) -> PrimaryFireBehaviourResult:
    """Calculate head fire intensity from the primary CFFDRS FBP fields."""
    fuel, _ = datasets.fuel.replace_nodata_with(np.nan)
    ffmc, _ = datasets.ffmc.replace_nodata_with(np.nan)
    bui, _ = datasets.bui.replace_nodata_with(np.nan)
    wind_speed, _ = datasets.wind_speed.replace_nodata_with(np.nan)
    wind_direction, _ = datasets.wind_direction.replace_nodata_with(np.nan)
    fmc, _ = datasets.fmc.replace_nodata_with(np.nan)
    isi, _ = datasets.isi.replace_nodata_with(np.nan)
    percent_conifer, _ = datasets.percent_conifer.replace_nodata_with(np.nan)

    if datasets.slope is None:
        slope = np.zeros_like(fuel, dtype=np.float32)
    else:
        slope, _ = datasets.slope.replace_nodata_with(np.nan)
    if datasets.aspect is None:
        aspect = np.zeros_like(fuel, dtype=np.float32)
    else:
        aspect, _ = datasets.aspect.replace_nodata_with(np.nan)

    fuel_type_codes = fuel_type_codes_from_grid(fuel)
    validate_percent_conifer(fuel, percent_conifer)

    non_combustible_mask = np.isin(fuel, tuple(NON_COMBUSTIBLE_FUEL_VALUES))
    calculation_mask = (
        ~non_combustible_mask
        & (fuel_type_codes != NODATA_FUEL_TYPE_CODE)
        & np.isfinite(ffmc)
        & np.isfinite(bui)
        & np.isfinite(wind_speed)
        & np.isfinite(wind_direction)
        & np.isfinite(slope)
        & np.isfinite(aspect)
        & np.isfinite(fmc)
        & np.isfinite(isi)
    )

    output = np.full(fuel.shape, SFMS_NO_DATA, dtype=np.float32)
    if np.any(calculation_mask):
        start = perf_counter()
        pdf = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        cc = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        gfl = np.full(fuel[calculation_mask].shape, 0.35, dtype=np.float32)
        cbh = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        cfl = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        lat = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        lon = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        elv = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        dj = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        d0 = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        sd = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        sh = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        hr = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        theta_rad = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        accel = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        buieff = np.ones_like(fuel[calculation_mask], dtype=np.float32)

        primary = vectorized_primary_fire_behaviour_prediction(
            fuel_type_codes[calculation_mask],
            ffmc[calculation_mask],
            bui[calculation_mask],
            wind_speed[calculation_mask],
            wind_direction[calculation_mask],
            slope[calculation_mask],
            aspect[calculation_mask],
            percent_conifer[calculation_mask],
            pdf,
            cc,
            gfl,
            cbh,
            cfl,
            fmc[calculation_mask],
            isi[calculation_mask],
            lat,
            lon,
            elv,
            dj,
            d0,
            sd,
            sh,
            hr,
            theta_rad,
            accel,
            buieff,
        )
        logger.info("%f seconds to calculate vectorized primary FBP", perf_counter() - start)
        output[calculation_mask] = np.where(np.isfinite(primary.hfi), primary.hfi, SFMS_NO_DATA)

    output[non_combustible_mask] = 0
    return PrimaryFireBehaviourResult(output)


class PrimaryFireBehaviourProcessor:
    """Load, validate, calculate, and publish one daily primary FBP raster."""

    def __init__(self, datetime_to_process: datetime):
        self.datetime_to_process = datetime_to_process
        self._raster_dependencies = GriddedRasterDependencies()

    @staticmethod
    def _dependency_keys(inputs: PrimaryFireBehaviourInputs) -> tuple[GDALPath, ...]:
        dependencies = [
            inputs.fuel_key,
            inputs.ffmc_key,
            inputs.bui_key,
            inputs.wind_speed_key,
            inputs.wind_direction_key,
            inputs.percent_conifer_key,
            inputs.fmc_key,
            inputs.isi_key,
        ]
        if inputs.slope_key is not None:
            dependencies.append(inputs.slope_key)
        if inputs.aspect_key is not None:
            dependencies.append(inputs.aspect_key)
        return tuple(dependencies)

    @contextmanager
    def _open_datasets(
        self,
        input_dataset_context: MultiDatasetContext,
        inputs: PrimaryFireBehaviourInputs,
    ) -> Generator[PrimaryFireBehaviourDatasets, None, None]:
        with self._raster_dependencies.open_by_key(
            input_dataset_context, self._dependency_keys(inputs)
        ) as datasets_by_key:
            slope = (
                datasets_by_key[inputs.slope_key]
                if inputs.slope_key is not None
                else None
            )
            aspect = (
                datasets_by_key[inputs.aspect_key]
                if inputs.aspect_key is not None
                else None
            )
            yield PrimaryFireBehaviourDatasets(
                fuel=datasets_by_key[inputs.fuel_key],
                ffmc=datasets_by_key[inputs.ffmc_key],
                bui=datasets_by_key[inputs.bui_key],
                wind_speed=datasets_by_key[inputs.wind_speed_key],
                wind_direction=datasets_by_key[inputs.wind_direction_key],
                slope=slope,
                aspect=aspect,
                percent_conifer=datasets_by_key[inputs.percent_conifer_key],
                fmc=datasets_by_key[inputs.fmc_key],
                isi=datasets_by_key[inputs.isi_key],
            )

    def _validate_grids(self, datasets: PrimaryFireBehaviourDatasets) -> None:
        grid_map = {
            "ffmc": datasets.ffmc,
            "bui": datasets.bui,
            "wind_speed": datasets.wind_speed,
            "wind_direction": datasets.wind_direction,
            "percent_conifer": datasets.percent_conifer,
            "fmc": datasets.fmc,
            "isi": datasets.isi,
        }
        if datasets.slope is not None:
            grid_map["slope"] = datasets.slope
        if datasets.aspect is not None:
            grid_map["aspect"] = datasets.aspect
        self._raster_dependencies.validate_grids(datasets.fuel, grid_map)

    async def process(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        inputs: PrimaryFireBehaviourInputs,
    ) -> None:
        """Calculate and publish the shared primary FBP output raster."""
        with gdal_s3_context():
            await self._raster_dependencies.assert_keys_exist(
                s3_client,
                self._dependency_keys(inputs),
            )
            logger.info(
                "Calculating primary FBP %s for %s",
                inputs.run_type.value,
                self.datetime_to_process.date(),
            )

            with self._open_datasets(input_dataset_context, inputs) as datasets:
                self._validate_grids(datasets)
                result = calculate_primary_fire_behaviour(datasets)

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
                    output_band.SetDescription("head_fire_intensity")
                    output_band.SetUnitType("kW/m")
                    published = await publish_dataset(
                        s3_client=s3_client,
                        dataset=output_ds,
                        output_key=inputs.output_key,
                    )

            logger.info(
                "Stored HFI %s: %s (COG: %s)",
                inputs.run_type.value,
                published.output_key,
                published.cog_key,
            )
