"""Raster processor for shared daily Foliar Moisture Content calculations."""

import logging
from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from time import perf_counter
from typing import Callable, ContextManager, Generator, Mapping

import numpy as np
from cffdrs_vec.fbp import vectorized_foliar_moisture_content
from wps_shared.geospatial.geospatial import rasters_match
from wps_shared.geospatial.wps_dataset import WPSDataset, multi_wps_dataset_context
from wps_shared.sfms.raster_addresser import GDALPath
from wps_shared.utils.s3 import gdal_s3_context
from wps_shared.utils.s3_client import S3Client

from wps_sfms.interpolation.common import SFMS_NO_DATA
from wps_sfms.publish import publish_dataset
from wps_sfms.raster_inputs import FoliarMoistureContentInputs
from wps_sfms.raster_output import create_masked_output_dataset
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

logger = logging.getLogger(__name__)

MultiDatasetContext = Callable[[list[str]], ContextManager[list[WPSDataset]]]


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
    """Load shared static inputs once and publish FMC for one or more dates."""

    @staticmethod
    async def _assert_dependencies_exist(
        s3_client: S3Client,
        inputs: FoliarMoistureContentInputs,
    ) -> None:
        dependency_keys = (
            inputs.fuel_key,
            inputs.elevation_key,
            inputs.latitude_key,
            inputs.longitude_key,
        )
        if not await s3_client.all_objects_exist(*dependency_keys):
            details = ", ".join(str(key) for key in dependency_keys)
            raise RuntimeError(f"Missing FMC dependencies: {details}")

    @contextmanager
    def _open_datasets(
        self,
        input_dataset_context: MultiDatasetContext,
        inputs: FoliarMoistureContentInputs,
    ) -> Generator[FoliarMoistureContentDatasets, None, None]:
        keys = [
            inputs.fuel_key,
            inputs.elevation_key,
            inputs.latitude_key,
            inputs.longitude_key,
        ]
        with input_dataset_context(keys) as input_datasets:
            datasets_by_key = {dataset.ds_path: dataset for dataset in input_datasets}
            yield FoliarMoistureContentDatasets(
                fuel=datasets_by_key[inputs.fuel_key],
                elevation=datasets_by_key[inputs.elevation_key],
                latitude=datasets_by_key[inputs.latitude_key],
                longitude=datasets_by_key[inputs.longitude_key],
            )

    @staticmethod
    def _validate_grids(
        datasets: FoliarMoistureContentDatasets,
        inputs: FoliarMoistureContentInputs,
    ) -> None:
        reference = datasets.fuel.as_gdal_ds()
        candidates = (
            ("elevation", inputs.elevation_key, datasets.elevation),
            ("latitude", inputs.latitude_key, datasets.latitude),
            ("longitude", inputs.longitude_key, datasets.longitude),
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
        inputs: FoliarMoistureContentInputs,
    ) -> None:
        """Calculate and publish every requested FMC date from the shared static inputs."""
        if not inputs.output_keys:
            return

        with gdal_s3_context():
            await self._assert_dependencies_exist(s3_client, inputs)
            with self._open_datasets(input_dataset_context, inputs) as datasets:
                self._validate_grids(datasets, inputs)

                for target_date, output_key in inputs.output_keys.items():
                    result = calculate_foliar_moisture_content(datasets, target_date)
                    with create_masked_output_dataset(
                        result.values,
                        datasets.fuel,
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


async def ensure_fmc_rasters(
    target_dates: Iterable[date],
    fuel_key: GDALPath,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
) -> None:
    """Validate complete FMC rasters and publish dates without exisiting FMC rasters."""
    unique_dates = tuple(dict.fromkeys(target_dates))
    missing_dates = []
    existing_fmc_keys: dict[date, GDALPath] = {}
    for target_date in unique_dates:
        output_key = raster_addresser.get_fmc_key(target_date)
        cog_key = raster_addresser.get_cog_key(output_key)
        if await s3_client.all_objects_exist(output_key, cog_key):
            logger.info("Skipping existing FMC raster for %s: %s", target_date, output_key)
            existing_fmc_keys[target_date] = raster_addresser.gdal_path(output_key)
        else:
            missing_dates.append(target_date)

    if existing_fmc_keys:
        with gdal_s3_context():
            _validate_existing_fmc_grids(fuel_key, existing_fmc_keys)

    if not missing_dates:
        return

    inputs = raster_addresser.get_fmc_inputs(missing_dates, fuel_key)
    processor = FoliarMoistureContentProcessor()
    await processor.process(s3_client, multi_wps_dataset_context, inputs)
