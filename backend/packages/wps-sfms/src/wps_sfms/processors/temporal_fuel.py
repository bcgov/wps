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
from wps_shared.schemas.sfms import FuelCode, FuelCodesLookup
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
    # values used by temporal fuel grids. Leafless/matted variants are the off-season defaults.
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

    # national FBP fuel lookup rows for the grid values temporal fuel grids can contain; written
    # alongside each temporal fuel grid so consumers can label and colour it.
    NATIONAL_FUEL_LOOKUP: ClassVar[Mapping[int, FuelCode]] = MappingProxyType(
        {
            fuel_code.grid_value: fuel_code
            for fuel_code in (
                FuelCode(
                    grid_value=1,
                    export_value=1,
                    descriptive_name="Spruce-Lichen Woodland",
                    fuel_type="C-1",
                    red=209,
                    green=255,
                    blue=115,
                    hue=57,
                    saturation=255,
                    lightness=185,
                ),
                FuelCode(
                    grid_value=2,
                    export_value=2,
                    descriptive_name="Boreal Spruce",
                    fuel_type="C-2",
                    red=34,
                    green=102,
                    blue=51,
                    hue=95,
                    saturation=128,
                    lightness=68,
                ),
                FuelCode(
                    grid_value=3,
                    export_value=3,
                    descriptive_name="Mature Jack or Lodgepole Pine",
                    fuel_type="C-3",
                    red=131,
                    green=199,
                    blue=149,
                    hue=96,
                    saturation=96,
                    lightness=165,
                ),
                FuelCode(
                    grid_value=4,
                    export_value=4,
                    descriptive_name="Immature Jack or Lodgepole Pine",
                    fuel_type="C-4",
                    red=112,
                    green=168,
                    blue=0,
                    hue=57,
                    saturation=255,
                    lightness=84,
                ),
                FuelCode(
                    grid_value=5,
                    export_value=5,
                    descriptive_name="Red and White Pine",
                    fuel_type="C-5",
                    red=223,
                    green=184,
                    blue=230,
                    hue=206,
                    saturation=122,
                    lightness=207,
                ),
                FuelCode(
                    grid_value=6,
                    export_value=6,
                    descriptive_name="Conifer Plantation",
                    fuel_type="C-6",
                    red=172,
                    green=102,
                    blue=237,
                    hue=192,
                    saturation=201,
                    lightness=170,
                ),
                FuelCode(
                    grid_value=7,
                    export_value=7,
                    descriptive_name="Ponderosa Pine - Douglas-Fir",
                    fuel_type="C-7",
                    red=112,
                    green=12,
                    blue=242,
                    hue=188,
                    saturation=231,
                    lightness=127,
                ),
                FuelCode(
                    grid_value=11,
                    export_value=11,
                    descriptive_name="Leafless Aspen",
                    fuel_type="D-1",
                    red=196,
                    green=189,
                    blue=151,
                    hue=35,
                    saturation=70,
                    lightness=174,
                ),
                FuelCode(
                    grid_value=12,
                    export_value=12,
                    descriptive_name="Green Aspen (with BUI Thresholding)",
                    fuel_type="D-2",
                    red=137,
                    green=112,
                    blue=68,
                    hue=27,
                    saturation=86,
                    lightness=103,
                ),
                FuelCode(
                    grid_value=21,
                    export_value=21,
                    descriptive_name="Jack or Lodgepole Pine Slash",
                    fuel_type="S-1",
                    red=251,
                    green=190,
                    blue=185,
                    hue=3,
                    saturation=227,
                    lightness=218,
                ),
                FuelCode(
                    grid_value=22,
                    export_value=22,
                    descriptive_name="White Spruce - Balsam Slash",
                    fuel_type="S-2",
                    red=247,
                    green=104,
                    blue=161,
                    hue=238,
                    saturation=229,
                    lightness=176,
                ),
                FuelCode(
                    grid_value=23,
                    export_value=23,
                    descriptive_name="Coastal Cedar - Hemlock - Douglas-Fir Slash",
                    fuel_type="S-3",
                    red=174,
                    green=1,
                    blue=126,
                    hue=225,
                    saturation=252,
                    lightness=88,
                ),
                FuelCode(
                    grid_value=31,
                    export_value=31,
                    descriptive_name="Matted Grass",
                    fuel_type="O-1a",
                    red=255,
                    green=255,
                    blue=190,
                    hue=42,
                    saturation=255,
                    lightness=223,
                ),
                FuelCode(
                    grid_value=32,
                    export_value=32,
                    descriptive_name="Standing Grass",
                    fuel_type="O-1b",
                    red=230,
                    green=230,
                    blue=0,
                    hue=42,
                    saturation=255,
                    lightness=115,
                ),
                FuelCode(
                    grid_value=40,
                    export_value=40,
                    descriptive_name="Boreal Mixedwood - Leafless",
                    fuel_type="M-1",
                    red=255,
                    green=211,
                    blue=127,
                    hue=28,
                    saturation=255,
                    lightness=191,
                ),
                FuelCode(
                    grid_value=50,
                    export_value=50,
                    descriptive_name="Boreal Mixedwood - Green",
                    fuel_type="M-2",
                    red=255,
                    green=170,
                    blue=0,
                    hue=28,
                    saturation=255,
                    lightness=128,
                ),
                FuelCode(
                    grid_value=70,
                    export_value=70,
                    descriptive_name="Dead Balsam Fir Mixedwood - Leafless",
                    fuel_type="M-3",
                    red=99,
                    green=0,
                    blue=0,
                    hue=0,
                    saturation=255,
                    lightness=50,
                ),
                FuelCode(
                    grid_value=80,
                    export_value=80,
                    descriptive_name="Dead Balsam Fir Mixedwood - Green",
                    fuel_type="M-4",
                    red=170,
                    green=0,
                    blue=0,
                    hue=0,
                    saturation=255,
                    lightness=85,
                ),
                FuelCode(
                    grid_value=101,
                    export_value=101,
                    descriptive_name="Non-fuel",
                    fuel_type="Non-fuel",
                    red=130,
                    green=130,
                    blue=130,
                    hue=170,
                    saturation=0,
                    lightness=130,
                ),
                FuelCode(
                    grid_value=102,
                    export_value=102,
                    descriptive_name="Water",
                    fuel_type="Non-fuel",
                    red=115,
                    green=223,
                    blue=255,
                    hue=138,
                    saturation=255,
                    lightness=185,
                ),
            )
        }
    )

    values: np.ndarray
    """National fuel grid values, with NaN where the base fuel grid has no data."""

    @classmethod
    def build(cls, datasets: TemporalFuelInputDatasets, target_date: date) -> "TemporalFuelGrid":
        """Build the grid for ``target_date``, applying green-up and then grass curing.

        A pixel is green when ``green_up_on <= day of year < green_up_off``, and its grass is
        standing when ``grass_standing <= day of year < grass_matted``. Julian date nodata pixels
        never switch. A ``ValueError`` is raised for unrecognized base fuel values.
        """
        base_fuel, _ = datasets.base_fuel.replace_nodata_with(np.nan)
        green_up_on, _ = datasets.julian.green_up_on.replace_nodata_with(np.nan)
        green_up_off, _ = datasets.julian.green_up_off.replace_nodata_with(np.nan)
        grass_standing, _ = datasets.julian.grass_standing.replace_nodata_with(np.nan)
        grass_matted, _ = datasets.julian.grass_matted.replace_nodata_with(np.nan)

        values = np.full(base_fuel.shape, np.nan, dtype=np.float32)
        for bc_value, national_value in cls.NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE.items():
            values[base_fuel == bc_value] = national_value

        unrecognized = np.isfinite(base_fuel) & np.isnan(values)
        if np.any(unrecognized):
            unsupported = sorted(np.unique(base_fuel[unrecognized]).tolist())
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
            values[green & (values == leafless_value)] = green_value

        standing = (grass_standing <= day_of_year) & (day_of_year < grass_matted)
        for matted_value, standing_value in cls.GRASS_STANDING_GRID_VALUES.items():
            values[standing & (values == matted_value)] = standing_value
        return cls(values)

    def fuel_codes_lookup(self) -> FuelCodesLookup:
        """Return the national fuel lookup rows for the grid values present in this grid."""
        grid_values = np.unique(self.values[np.isfinite(self.values)]).astype(int).tolist()
        return FuelCodesLookup(
            fuel_codes=[self.NATIONAL_FUEL_LOOKUP[value] for value in grid_values]
        )


async def publish_temporal_fuel_raster(
    s3_client: S3Client,
    target_date: date,
    *,
    base_fuel_key: GDALPath,
    julian: JulianDatasets,
    output_key: S3Key,
    fuel_codes_lookup_key: S3Key,
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

    await s3_client.put_object(
        key=fuel_codes_lookup_key, body=grid.fuel_codes_lookup().model_dump_json().encode()
    )
    logger.info(
        "Stored temporal fuel raster for %s: %s (COG: %s, fuel codes lookup: %s)",
        target_date,
        published.output_key,
        published.cog_key,
        fuel_codes_lookup_key,
    )
    return published.content_hash
