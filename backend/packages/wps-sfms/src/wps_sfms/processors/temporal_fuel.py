"""Build daily temporal fuel grids from the BC base fuel grid and Julian-date season rasters.

The temporal grid translates BC base fuel values to national FBP fuel lookup values, then
applies green-up so leafless deciduous and mixedwood fuels become their green variants on
dates inside each pixel's green-up period.
"""

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

from wps_sfms.publish import publish_dataset
from wps_sfms.raster_dependencies import GriddedRasterDependencies

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TemporalFuelInputDatasets:
    base_fuel: WPSDataset
    green_up_on: WPSDataset
    green_up_off: WPSDataset
    grass_standing: WPSDataset
    grass_matted: WPSDataset


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
                    r=209,
                    g=255,
                    b=115,
                    h=57,
                    s=255,
                    l=185,
                ),
                FuelCode(
                    grid_value=2,
                    export_value=2,
                    descriptive_name="Boreal Spruce",
                    fuel_type="C-2",
                    r=34,
                    g=102,
                    b=51,
                    h=95,
                    s=128,
                    l=68,
                ),
                FuelCode(
                    grid_value=3,
                    export_value=3,
                    descriptive_name="Mature Jack or Lodgepole Pine",
                    fuel_type="C-3",
                    r=131,
                    g=199,
                    b=149,
                    h=96,
                    s=96,
                    l=165,
                ),
                FuelCode(
                    grid_value=4,
                    export_value=4,
                    descriptive_name="Immature Jack or Lodgepole Pine",
                    fuel_type="C-4",
                    r=112,
                    g=168,
                    b=0,
                    h=57,
                    s=255,
                    l=84,
                ),
                FuelCode(
                    grid_value=5,
                    export_value=5,
                    descriptive_name="Red and White Pine",
                    fuel_type="C-5",
                    r=223,
                    g=184,
                    b=230,
                    h=206,
                    s=122,
                    l=207,
                ),
                FuelCode(
                    grid_value=6,
                    export_value=6,
                    descriptive_name="Conifer Plantation",
                    fuel_type="C-6",
                    r=172,
                    g=102,
                    b=237,
                    h=192,
                    s=201,
                    l=170,
                ),
                FuelCode(
                    grid_value=7,
                    export_value=7,
                    descriptive_name="Ponderosa Pine - Douglas-Fir",
                    fuel_type="C-7",
                    r=112,
                    g=12,
                    b=242,
                    h=188,
                    s=231,
                    l=127,
                ),
                FuelCode(
                    grid_value=11,
                    export_value=11,
                    descriptive_name="Leafless Aspen",
                    fuel_type="D-1",
                    r=196,
                    g=189,
                    b=151,
                    h=35,
                    s=70,
                    l=174,
                ),
                FuelCode(
                    grid_value=12,
                    export_value=12,
                    descriptive_name="Green Aspen (with BUI Thresholding)",
                    fuel_type="D-2",
                    r=137,
                    g=112,
                    b=68,
                    h=27,
                    s=86,
                    l=103,
                ),
                FuelCode(
                    grid_value=21,
                    export_value=21,
                    descriptive_name="Jack or Lodgepole Pine Slash",
                    fuel_type="S-1",
                    r=251,
                    g=190,
                    b=185,
                    h=3,
                    s=227,
                    l=218,
                ),
                FuelCode(
                    grid_value=22,
                    export_value=22,
                    descriptive_name="White Spruce - Balsam Slash",
                    fuel_type="S-2",
                    r=247,
                    g=104,
                    b=161,
                    h=238,
                    s=229,
                    l=176,
                ),
                FuelCode(
                    grid_value=23,
                    export_value=23,
                    descriptive_name="Coastal Cedar - Hemlock - Douglas-Fir Slash",
                    fuel_type="S-3",
                    r=174,
                    g=1,
                    b=126,
                    h=225,
                    s=252,
                    l=88,
                ),
                FuelCode(
                    grid_value=31,
                    export_value=31,
                    descriptive_name="Matted Grass",
                    fuel_type="O-1a",
                    r=255,
                    g=255,
                    b=190,
                    h=42,
                    s=255,
                    l=223,
                ),
                FuelCode(
                    grid_value=32,
                    export_value=32,
                    descriptive_name="Standing Grass",
                    fuel_type="O-1b",
                    r=230,
                    g=230,
                    b=0,
                    h=42,
                    s=255,
                    l=115,
                ),
                FuelCode(
                    grid_value=40,
                    export_value=40,
                    descriptive_name="Boreal Mixedwood - Leafless",
                    fuel_type="M-1",
                    r=255,
                    g=211,
                    b=127,
                    h=28,
                    s=255,
                    l=191,
                ),
                FuelCode(
                    grid_value=50,
                    export_value=50,
                    descriptive_name="Boreal Mixedwood - Green",
                    fuel_type="M-2",
                    r=255,
                    g=170,
                    b=0,
                    h=28,
                    s=255,
                    l=128,
                ),
                FuelCode(
                    grid_value=70,
                    export_value=70,
                    descriptive_name="Dead Balsam Fir Mixedwood - Leafless",
                    fuel_type="M-3",
                    r=99,
                    g=0,
                    b=0,
                    h=0,
                    s=255,
                    l=50,
                ),
                FuelCode(
                    grid_value=80,
                    export_value=80,
                    descriptive_name="Dead Balsam Fir Mixedwood - Green",
                    fuel_type="M-4",
                    r=170,
                    g=0,
                    b=0,
                    h=0,
                    s=255,
                    l=85,
                ),
                FuelCode(
                    grid_value=101,
                    export_value=101,
                    descriptive_name="Non-fuel",
                    fuel_type="Non-fuel",
                    r=130,
                    g=130,
                    b=130,
                    h=170,
                    s=0,
                    l=130,
                ),
                FuelCode(
                    grid_value=102,
                    export_value=102,
                    descriptive_name="Water",
                    fuel_type="Non-fuel",
                    r=115,
                    g=223,
                    b=255,
                    h=138,
                    s=255,
                    l=185,
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
        green_up_on, _ = datasets.green_up_on.replace_nodata_with(np.nan)
        green_up_off, _ = datasets.green_up_off.replace_nodata_with(np.nan)
        grass_standing, _ = datasets.grass_standing.replace_nodata_with(np.nan)
        grass_matted, _ = datasets.grass_matted.replace_nodata_with(np.nan)

        values = np.full(base_fuel.shape, np.nan, dtype=np.float32)
        for bc_value, national_value in cls.NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE.items():
            values[base_fuel == bc_value] = national_value

        unrecognized = np.isfinite(base_fuel) & np.isnan(values)
        if np.any(unrecognized):
            unsupported = sorted(np.unique(base_fuel[unrecognized]).tolist())
            raise ValueError(
                f"Base fuel raster contains unsupported classifications: {unsupported}"
            )

        day_of_year = target_date.timetuple().tm_yday
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
    green_up_on_key: GDALPath,
    green_up_off_key: GDALPath,
    grass_standing_key: GDALPath,
    grass_matted_key: GDALPath,
    output_key: S3Key,
    fuel_codes_lookup_path: S3Key,
) -> str:
    """Calculate, store and return the content hash of the temporal fuel raster for one date.

    The raster keeps the base grid's geometry, data type and nodata value. Its COG uses
    nearest-neighbour resampling so fuel classifications are not blended.
    """
    dependencies = GriddedRasterDependencies()
    with gdal_s3_context():
        await dependencies.assert_keys_exist(
            s3_client,
            (
                base_fuel_key,
                green_up_on_key,
                green_up_off_key,
                grass_standing_key,
                grass_matted_key,
            ),
        )
        with (
            WPSDataset(base_fuel_key) as base_fuel,
            WPSDataset(green_up_on_key) as green_up_on,
            WPSDataset(green_up_off_key) as green_up_off,
            WPSDataset(grass_standing_key) as grass_standing,
            WPSDataset(grass_matted_key) as grass_matted,
        ):
            dependencies.validate_grids(
                base_fuel,
                {
                    "green_up_on": green_up_on,
                    "green_up_off": green_up_off,
                    "grass_standing": grass_standing,
                    "grass_matted": grass_matted,
                },
            )
            grid = TemporalFuelGrid.build(
                TemporalFuelInputDatasets(
                    base_fuel, green_up_on, green_up_off, grass_standing, grass_matted
                ),
                target_date,
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
        key=fuel_codes_lookup_path, body=grid.fuel_codes_lookup().model_dump_json().encode()
    )
    logger.info(
        "Stored temporal fuel raster for %s: %s (COG: %s, fuel codes lookup: %s)",
        target_date,
        published.output_key,
        published.cog_key,
        fuel_codes_lookup_path,
    )
    return await s3_client.get_content_hash(output_key)
