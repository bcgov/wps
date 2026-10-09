"""Build daily temporal fuel grids from the BC base fuel grid and Julian-date season rasters.

The temporal grid translates BC base fuel values to national FBP fuel lookup values, then
applies green-up so leafless deciduous and mixedwood fuels become their green variants inside
each pixel's green-up period, and grass curing so matted grass becomes standing grass inside
each pixel's standing period.
"""

import calendar
import logging
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import ClassVar, Mapping

import numpy as np
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import GDALPath, S3Key
from wps_shared.utils.s3 import gdal_s3_context
from wps_shared.utils.s3_client import S3Client

from wps_sfms.julian_rasters import JulianDatasets
from wps_sfms.publish import publish_dataset
from wps_sfms.raster_dependencies import GriddedRasterDependencies

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TemporalFuelInputDatasets:
    base_fuel: WPSDataset
    julian: JulianDatasets


@dataclass(frozen=True, eq=False)
class TemporalFuelGrid:
    """A day's fuel grid in national FBP lookup grid values, built from the BC base fuel grid.

    BC base values are translated to national values. Green-up then turns leafless D1, M1 and M3
    into D2, M2 and M4 wherever the date is inside the pixel's green-up period, and grass curing
    turns matted O1A into standing O1B wherever the date is inside the pixel's standing period.
    """

    # BC base fuel grid values (fuel_type_raster) translated to the national FBP fuel lookup grid
    # values (wps_shared.sfms.national_fuel_lookup) used by temporal fuel grids.
    # Leafless/matted variants are the off-season defaults.
    NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE: ClassVar[Mapping[int, int]] = MappingProxyType(
        {
            1: 1,  # C-1
            2: 2,  # C-2
            3: 3,  # C-3
            4: 4,  # C-4
            5: 5,  # C-5
            6: 6,  # C-6
            7: 7,  # C-7
            8: 11,  # D-1
            9: 21,  # S-1
            10: 22,  # S-2
            11: 23,  # S-3
            12: 31,  # O-1a
            13: 70,  # M-3
            14: 40,  # M-1
            99: 101,  # Non-fuel
            102: 102,  # Water
        }
    )

    # national grid values swapped from leafless to green during the green-up period
    GREEN_UP_GRID_VALUES: ClassVar[Mapping[int, int]] = MappingProxyType({11: 12, 40: 50, 70: 80})

    # national grid values swapped from matted to standing grass during the standing period
    GRASS_STANDING_GRID_VALUES: ClassVar[Mapping[int, int]] = MappingProxyType({31: 32})

    values: np.ndarray
    """National fuel grid values, with NaN where the base fuel grid has no data."""

    @classmethod
    def build(cls, datasets: TemporalFuelInputDatasets, target_date: date) -> "TemporalFuelGrid":
        """Build the grid for ``target_date``, applying green-up and then grass curing.

        A pixel is green when ``green_up_on <= day of year < green_up_off``, and its grass is
        standing when ``grass_standing <= day of year < grass_matted``. Julian date nodata pixels
        never switch. A ``ValueError`` is raised for unrecognized base fuel values.
        """
        bc_values, _ = datasets.base_fuel.replace_nodata_with(np.nan)
        green_up_on, _ = datasets.julian.green_up_on.replace_nodata_with(np.nan)
        green_up_off, _ = datasets.julian.green_up_off.replace_nodata_with(np.nan)
        grass_standing, _ = datasets.julian.grass_standing.replace_nodata_with(np.nan)
        grass_matted, _ = datasets.julian.grass_matted.replace_nodata_with(np.nan)

        temporal_fuel_values = np.full(bc_values.shape, np.nan, dtype=np.float32)
        for bc_value, national_value in cls.NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE.items():
            temporal_fuel_values[bc_values == bc_value] = national_value

        unrecognized = np.isfinite(bc_values) & np.isnan(temporal_fuel_values)
        if np.any(unrecognized):
            unsupported = sorted(np.unique(bc_values[unrecognized]).tolist())
            raise ValueError(
                f"Base fuel raster contains unsupported classifications: {unsupported}"
            )

        # the Julian date rasters number days as in a non-leap year (152 is Jun 1), so drop Feb 29
        # from the count in leap years; Feb 29 itself counts as Feb 28
        day_of_year = target_date.timetuple().tm_yday
        if calendar.isleap(target_date.year) and day_of_year > 59:
            day_of_year -= 1
        green = (green_up_on <= day_of_year) & (day_of_year < green_up_off)
        for leafless_value, green_value in cls.GREEN_UP_GRID_VALUES.items():
            temporal_fuel_values[green & (temporal_fuel_values == leafless_value)] = green_value

        standing = (grass_standing <= day_of_year) & (day_of_year < grass_matted)
        for matted_value, standing_value in cls.GRASS_STANDING_GRID_VALUES.items():
            temporal_fuel_values[standing & (temporal_fuel_values == matted_value)] = standing_value
        return cls(temporal_fuel_values)


async def publish_temporal_fuel_raster(
    s3_client: S3Client,
    target_date: date,
    *,
    base_fuel_key: GDALPath,
    julian: JulianDatasets,
    output_key: S3Key,
) -> str:
    """Calculate, store and return the content hash of the temporal fuel raster for one date.

    The Julian date rasters are passed in already open, so the caller can build them from the
    same bytes it hashed. The raster keeps the base grid's geometry, data type and nodata value.
    Its COG uses nearest-neighbour resampling so fuel classifications are not blended.
    """
    dependencies = GriddedRasterDependencies()
    with gdal_s3_context():
        await dependencies.assert_keys_exist(s3_client, (base_fuel_key,))
        with WPSDataset(base_fuel_key) as base_fuel:
            dependencies.validate_grids(base_fuel, julian.by_name())
            grid = TemporalFuelGrid.build(
                TemporalFuelInputDatasets(base_fuel=base_fuel, julian=julian), target_date
            )

            nodata_value = base_fuel.require_nodata_value()
            band = base_fuel.as_gdal_ds().GetRasterBand(1)
            with WPSDataset.from_array(
                np.where(np.isnan(grid.values), nodata_value, grid.values),
                base_fuel,
                nodata_value,
                datatype=band.DataType,
            ) as output_ds:
                output_ds.as_gdal_ds().GetRasterBand(1).SetDescription("fbp_fuel_type")
                published = await publish_dataset(
                    s3_client,
                    output_ds,
                    output_key,
                    cog_resample_alg=GDALResamplingMethod.NEAREST_NEIGHBOUR,
                )

    logger.info(
        "Stored temporal fuel raster for %s: %s (COG: %s)",
        target_date,
        published.output_key,
        published.cog_key,
    )
    return published.content_hash
