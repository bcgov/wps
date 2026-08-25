"""Raster processor for shared daily Foliar Moisture Content calculations."""

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from time import perf_counter
from typing import Generator, Mapping

import numpy as np
from cffdrs_vec.fbp import vectorized_foliar_moisture_content
from wps_shared.geospatial.geospatial import rasters_match
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import GDALPath, S3Key
from wps_shared.utils.s3 import gdal_s3_context
from wps_shared.utils.s3_client import S3Client

from wps_sfms.interpolation.common import SFMS_NO_DATA
from wps_sfms.publish import publish_dataset
from wps_sfms.raster_dependencies import GriddedRasterDependencies, MultiDatasetContext
from wps_sfms.raster_inputs import FoliarMoistureContentInputs
from wps_sfms.raster_output import create_masked_output_dataset, open_bc_mask_dataset
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FoliarMoistureContentResult:
    values: np.ndarray
    nodata_value: float = SFMS_NO_DATA


@dataclass(frozen=True)
class FoliarMoistureContentDatasets:
    fuel: WPSDataset  # fuel is only used for grid validation, not in the FMC calculation
    elevation: WPSDataset
    latitude: WPSDataset
    longitude: WPSDataset


def calculate_foliar_moisture_content(
    datasets: FoliarMoistureContentDatasets,
    target_date: date,
) -> FoliarMoistureContentResult:
    """Calculate FMC for one calendar date wherever all static inputs are valid."""
    elevation, _ = datasets.elevation.replace_nodata_with(np.nan)
    latitude, _ = datasets.latitude.replace_nodata_with(np.nan)
    longitude, _ = datasets.longitude.replace_nodata_with(np.nan)

    calculation_mask = np.isfinite(elevation) & np.isfinite(latitude) & np.isfinite(longitude)
    output = np.full(elevation.shape, SFMS_NO_DATA, dtype=np.float32)
    if not np.any(calculation_mask):
        return FoliarMoistureContentResult(output)

    start = perf_counter()
    calculated = vectorized_foliar_moisture_content(
        latitude[calculation_mask],
        np.abs(longitude[calculation_mask]),
        elevation[calculation_mask],
        target_date.timetuple().tm_yday,
        0,
    )
    logger.info(
        "%f seconds to calculate vectorized FMC for %s",
        perf_counter() - start,
        target_date,
    )
    output[calculation_mask] = np.where(np.isfinite(calculated), calculated, SFMS_NO_DATA)
    return FoliarMoistureContentResult(output)


class FoliarMoistureContentProcessor:
    """Reuse existing FMC rasters and calculate missing dates from shared static inputs."""

    def __init__(self, raster_addresser: SFMSNGRasterAddresser):
        self.raster_addresser = raster_addresser
        self._raster_dependencies = GriddedRasterDependencies()

    @staticmethod
    def _dependency_keys(inputs: FoliarMoistureContentInputs) -> tuple[GDALPath, ...]:
        return (
            inputs.fuel_key,
            inputs.elevation_key,
            inputs.latitude_key,
            inputs.longitude_key,
        )

    @contextmanager
    def _open_datasets(
        self,
        input_dataset_context: MultiDatasetContext,
        inputs: FoliarMoistureContentInputs,
    ) -> Generator[FoliarMoistureContentDatasets, None, None]:
        with self._raster_dependencies.open_by_key(
            input_dataset_context, self._dependency_keys(inputs)
        ) as datasets_by_key:
            yield FoliarMoistureContentDatasets(
                fuel=datasets_by_key[inputs.fuel_key],
                elevation=datasets_by_key[inputs.elevation_key],
                latitude=datasets_by_key[inputs.latitude_key],
                longitude=datasets_by_key[inputs.longitude_key],
            )

    def _validate_grids(
        self,
        datasets: FoliarMoistureContentDatasets,
    ) -> None:
        self._raster_dependencies.validate_grids(
            datasets.fuel,
            {
                "elevation": datasets.elevation,
                "latitude": datasets.latitude,
                "longitude": datasets.longitude,
            },
        )

    @staticmethod
    def _validate_existing_fmc_grids(
        fuel_key: GDALPath,
        fmc_keys: Mapping[date, GDALPath],
    ) -> None:
        """Validate that existing FMC rasters use the selected fuel raster's grid.

        Each FMC raster must have the same pixel resolution, top-left origin, row and column
        dimensions, and equivalent projection as the fuel raster. This ensures its pixels can be
        combined directly with the fuel grid and other aligned FBP inputs.
        """
        with WPSDataset(fuel_key) as fuel:
            for target_date, fmc_key in fmc_keys.items():
                with WPSDataset(fmc_key) as fmc:
                    if not rasters_match(fmc.as_gdal_ds(), fuel.as_gdal_ds()):
                        raise ValueError(
                            f"Existing FMC raster for {target_date} does not match the fuel grid: "
                            f"{fmc_key} vs {fuel_key}"
                        )

    async def _select_outputs_to_process(
        self,
        s3_client: S3Client,
        fuel_key: GDALPath,
        output_keys: Mapping[date, S3Key],
    ) -> dict[date, S3Key]:
        """Return missing FMC outputs after validating complete existing outputs."""
        outputs_to_process = {}
        existing_fmc_keys: dict[date, GDALPath] = {}
        for target_date, output_key in output_keys.items():
            cog_key = self.raster_addresser.get_cog_key(output_key)
            if await s3_client.all_objects_exist(output_key, cog_key):
                logger.info(
                    "Skipping existing FMC raster for %s: %s",
                    target_date,
                    output_key,
                )
                existing_fmc_keys[target_date] = self.raster_addresser.gdal_path(output_key)
            else:
                outputs_to_process[target_date] = output_key

        if existing_fmc_keys:
            with gdal_s3_context():
                self._validate_existing_fmc_grids(fuel_key, existing_fmc_keys)

        return outputs_to_process

    async def process(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        inputs: FoliarMoistureContentInputs,
    ) -> None:
        """Reuse valid FMC rasters and calculate any requested dates that are missing."""
        if not inputs.output_keys:
            return

        outputs_to_process = await self._select_outputs_to_process(
            s3_client,
            inputs.fuel_key,
            inputs.output_keys,
        )
        if not outputs_to_process:
            return

        with gdal_s3_context():
            await self._raster_dependencies.assert_keys_exist(
                s3_client,
                self._dependency_keys(inputs),
            )
            with self._open_datasets(input_dataset_context, inputs) as datasets:
                self._validate_grids(datasets)

                with open_bc_mask_dataset() as mask:
                    for target_date, output_key in outputs_to_process.items():
                        result = calculate_foliar_moisture_content(datasets, target_date)
                        with create_masked_output_dataset(
                            result.values,
                            datasets.fuel,
                            mask,
                            result.nodata_value,
                        ) as output_ds:
                            output_band = output_ds.as_gdal_ds().GetRasterBand(1)
                            output_band.SetDescription("foliar_moisture_content")
                            output_band.SetUnitType("%")
                            published = await publish_dataset(
                                s3_client=s3_client,
                                dataset=output_ds,
                                output_key=output_key,
                            )

                        logger.info(
                            "Stored FMC for %s: %s (COG: %s)",
                            target_date,
                            published.output_key,
                            published.cog_key,
                        )
