"""Calculate and publish shared daily SFMS Fire Behaviour Prediction raster products.

One primary CFFDRS call produces surface fuel consumption (SFC), equilibrium head rate of
spread (ROS), and head fire intensity (HFI) from aligned SFMS input rasters.
"""

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Generator

import numpy as np
from cffdrs_vec.fbp import vectorized_primary_fire_behaviour_prediction
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import FBPParameter, GDALPath
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

MAX_GROUND_SLOPE_PERCENT = 70.0


@dataclass(frozen=True)
class PrimaryFireBehaviourResult:
    sfc: np.ndarray
    ros: np.ndarray
    hfi: np.ndarray
    nodata_value: float = SFMS_NO_DATA


@dataclass(frozen=True)
class PrimaryFireBehaviourDatasets:
    fuel: WPSDataset
    ffmc: WPSDataset
    bui: WPSDataset
    wind_speed: WPSDataset
    wind_direction: WPSDataset
    slope: WPSDataset
    aspect: WPSDataset
    percent_conifer: WPSDataset
    fmc: WPSDataset


def _result_values(
    calculated: np.ndarray,
    calculation_mask: np.ndarray,
    non_combustible_mask: np.ndarray,
) -> np.ndarray:
    """Map calculated pixels into the full grid using SFMS nodata and non-fuel policies."""
    output = np.full(calculation_mask.shape, SFMS_NO_DATA, dtype=np.float32)
    output[calculation_mask] = np.where(np.isfinite(calculated), calculated, SFMS_NO_DATA)
    output[non_combustible_mask] = 0
    return output


def calculate_primary_fire_behaviour(
    datasets: PrimaryFireBehaviourDatasets,
) -> PrimaryFireBehaviourResult:
    """Calculate SFC, equilibrium head ROS, and HFI on the shared raster grid.

    Wind direction and downslope aspect arrive in degrees and are normalized to radians here.
    Ground slope arrives as percent and is clamped to the legacy SFMS supported range
    of 0–70%. Only FMC values in ``(0, 120]`` are accepted, which prevents CFFDRS from deriving
    FMC from the placeholder location and date inputs. Passing zero for ISI makes CFFDRS derive
    it from FFMC and terrain-adjusted effective wind instead of using the FWI ISI raster.

    Pixels missing a required input produce ``SFMS_NO_DATA`` in every output. Recognized
    non-combustible fuel pixels produce zero regardless of other missing inputs.
    """
    fuel, _ = datasets.fuel.replace_nodata_with(np.nan)
    ffmc, _ = datasets.ffmc.replace_nodata_with(np.nan)
    bui, _ = datasets.bui.replace_nodata_with(np.nan)
    wind_speed, _ = datasets.wind_speed.replace_nodata_with(np.nan)
    wind_direction, _ = datasets.wind_direction.replace_nodata_with(np.nan)
    slope, _ = datasets.slope.replace_nodata_with(np.nan)
    aspect, _ = datasets.aspect.replace_nodata_with(np.nan)
    fmc, _ = datasets.fmc.replace_nodata_with(np.nan)
    percent_conifer, _ = datasets.percent_conifer.replace_nodata_with(np.nan)

    wind_direction_rad = np.radians(np.mod(wind_direction, 360.0))
    # clamp at 70% because CFFDRS uses the same maximum spread factor for every steeper slope, this also
    # matches legacy SFMS behaviour.
    slope_percent = np.clip(slope, 0.0, MAX_GROUND_SLOPE_PERCENT)

    aspect_is_valid = np.isfinite(aspect)
    aspect_rad = np.radians(np.mod(aspect, 360.0))
    # keep valid flat pixels deterministic even though aspect cannot affect their result
    aspect_rad = np.where(slope_percent == 0, 0.0, aspect_rad)

    fuel_type_codes = fuel_type_codes_from_grid(fuel)
    validate_percent_conifer(fuel, percent_conifer)

    non_combustible_mask = np.isin(fuel, tuple(NON_COMBUSTIBLE_FUEL_VALUES))
    calculation_mask = (
        ~non_combustible_mask
        & (fuel_type_codes != NODATA_FUEL_TYPE_CODE)
        & np.isfinite(ffmc)
        & np.isfinite(bui)
        & np.isfinite(wind_speed)
        & np.isfinite(wind_direction_rad)
        & np.isfinite(slope_percent)
        & aspect_is_valid
        & np.isfinite(fmc)
        & (fmc > 0)
        & (fmc <= 120)
    )

    if np.any(calculation_mask):
        start = perf_counter()
        pdf = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        cc = np.full(fuel[calculation_mask].shape, 65.0, dtype=np.float32)
        gfl = np.full(fuel[calculation_mask].shape, 0.35, dtype=np.float32)
        cbh = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        cfl = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        # valid FMC keeps CFFDRS from consulting these shared fallback placeholders
        fmc_fallback_placeholder = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        sd = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        sh = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        hr = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        theta_rad = np.zeros_like(fuel[calculation_mask], dtype=np.float32)
        accel = np.zeros_like(fuel[calculation_mask], dtype=np.int64)
        buieff = np.ones_like(fuel[calculation_mask], dtype=np.int64)
        isi = np.zeros_like(fuel[calculation_mask], dtype=np.float32)

        primary = vectorized_primary_fire_behaviour_prediction(
            fuel_type_codes[calculation_mask],
            ffmc[calculation_mask],
            bui[calculation_mask],
            wind_speed[calculation_mask],
            wind_direction_rad[calculation_mask],
            slope_percent[calculation_mask],
            aspect_rad[calculation_mask],
            percent_conifer[calculation_mask],
            pdf,
            cc,
            gfl,
            cbh,
            cfl,
            fmc[calculation_mask],
            isi,
            fmc_fallback_placeholder,  # latitude not needed, using fmc
            fmc_fallback_placeholder,  # longitude not needed, using fmc
            fmc_fallback_placeholder,  # elevation not needed, using fmc
            fmc_fallback_placeholder,  # julian date not needed, using fmc
            fmc_fallback_placeholder,  # julian date of minimum foliar moisture content not needed
            sd,
            sh,
            hr,
            theta_rad,
            accel,
            buieff,
        )
        logger.info("%f seconds to calculate vectorized primary FBP", perf_counter() - start)
        return PrimaryFireBehaviourResult(
            sfc=_result_values(primary.sfc, calculation_mask, non_combustible_mask),
            ros=_result_values(primary.ros, calculation_mask, non_combustible_mask),
            hfi=_result_values(primary.hfi, calculation_mask, non_combustible_mask),
        )

    empty_output = _result_values(
        np.empty(0, dtype=np.float32), calculation_mask, non_combustible_mask
    )
    return PrimaryFireBehaviourResult(
        sfc=empty_output,
        ros=empty_output,
        hfi=empty_output,
    )


class PrimaryFireBehaviourProcessor:
    """Validate aligned FBP inputs and publish daily SFC, ROS, and HFI rasters.

    All input grids must match the fuel grid. Each output preserves calculation nodata, encodes
    recognized non-combustible fuel as zero, and applies the BC boundary mask before publishing.
    """

    def __init__(self, datetime_to_process: datetime):
        self.datetime_to_process = datetime_to_process
        self._raster_dependencies = GriddedRasterDependencies()

    @staticmethod
    def _dependency_keys(inputs: PrimaryFireBehaviourInputs) -> tuple[GDALPath, ...]:
        return (
            inputs.fuel_key,
            inputs.ffmc_key,
            inputs.bui_key,
            inputs.wind_speed_key,
            inputs.wind_direction_key,
            inputs.slope_key,
            inputs.aspect_key,
            inputs.percent_conifer_key,
            inputs.fmc_key,
        )

    @contextmanager
    def _open_datasets(
        self,
        input_dataset_context: MultiDatasetContext,
        inputs: PrimaryFireBehaviourInputs,
    ) -> Generator[PrimaryFireBehaviourDatasets, None, None]:
        with self._raster_dependencies.open_by_key(
            input_dataset_context, self._dependency_keys(inputs)
        ) as datasets_by_key:
            yield PrimaryFireBehaviourDatasets(
                fuel=datasets_by_key[inputs.fuel_key],
                ffmc=datasets_by_key[inputs.ffmc_key],
                bui=datasets_by_key[inputs.bui_key],
                wind_speed=datasets_by_key[inputs.wind_speed_key],
                wind_direction=datasets_by_key[inputs.wind_direction_key],
                slope=datasets_by_key[inputs.slope_key],
                aspect=datasets_by_key[inputs.aspect_key],
                percent_conifer=datasets_by_key[inputs.percent_conifer_key],
                fmc=datasets_by_key[inputs.fmc_key],
            )

    def _validate_grids(self, datasets: PrimaryFireBehaviourDatasets) -> None:
        self._raster_dependencies.validate_grids(
            datasets.fuel,
            {
                "ffmc": datasets.ffmc,
                "bui": datasets.bui,
                "wind_speed": datasets.wind_speed,
                "wind_direction": datasets.wind_direction,
                "slope": datasets.slope,
                "aspect": datasets.aspect,
                "percent_conifer": datasets.percent_conifer,
                "fmc": datasets.fmc,
            },
        )

    async def process(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        inputs: PrimaryFireBehaviourInputs,
    ) -> None:
        """Calculate and publish the shared primary FBP output rasters."""
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

                outputs = (
                    (FBPParameter.SFC, result.sfc, "surface_fuel_consumption", "kg/m2"),
                    (FBPParameter.ROS, result.ros, "rate_of_spread", "m/min"),
                    (FBPParameter.HFI, result.hfi, "head_fire_intensity", "kW/m"),
                )
                with open_bc_mask_dataset() as mask:
                    for parameter, values, description, unit in outputs:
                        with create_masked_output_dataset(
                            values,
                            datasets.fuel,
                            mask,
                            result.nodata_value,
                        ) as output_ds:
                            output_band = output_ds.as_gdal_ds().GetRasterBand(1)
                            output_band.SetDescription(description)
                            output_band.SetUnitType(unit)
                            published = await publish_dataset(
                                s3_client=s3_client,
                                dataset=output_ds,
                                output_key=inputs.output_keys[parameter],
                            )
                            logger.info(
                                "Stored %s %s: %s (COG: %s)",
                                parameter.value.upper(),
                                inputs.run_type.value,
                                published.output_key,
                                published.cog_key,
                            )
