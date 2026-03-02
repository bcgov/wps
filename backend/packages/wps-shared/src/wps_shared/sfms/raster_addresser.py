import enum
from datetime import datetime
from typing import NewType

from wps_shared import config
from wps_shared.utils.time import assert_all_utc

# Distinct types for plain S3 keys vs GDAL vsis3-prefixed paths.
# Swapping them produces a silent runtime failure. These NewType aliases
# have no runtime enforcement — a type checker (pyright, mypy) is needed
# to catch misuse statically.
S3Key = NewType("S3Key", str)
GDALPath = NewType("GDALPath", str)


class SFMSInterpolatedWeatherParameter(enum.Enum):
    TEMP = "temperature"
    RH = "relative_humidity"
    WIND_SPEED = "wind_speed"
    PRECIP = "precipitation"


class FWIParameter(enum.Enum):
    DC = "dc"
    DMC = "dmc"
    BUI = "bui"
    FFMC = "ffmc"
    ISI = "isi"
    FWI = "fwi"


class BaseRasterAddresser:
    """S3/GDAL utilities shared across raster key addressers."""

    def __init__(self):
        self.s3_prefix = f"/vsis3/{config.get('OBJECT_STORE_BUCKET')}"

    def gdal_path(self, key: S3Key) -> GDALPath:
        """Return a GDAL vsis3-prefixed path for a plain S3 key."""
        return GDALPath(f"{self.s3_prefix}/{key}")

    def gdal_prefix_keys(self, *keys: S3Key) -> tuple[GDALPath, ...]:
        """Prefix keys with vsis3/{bucket} for reading from S3 with GDAL."""
        return tuple(self.gdal_path(key) for key in keys)

    def get_cog_key(self, key: S3Key) -> GDALPath:
        """Given a .tif key, return a GDAL-prefixed _cog.tif path."""
        if not key.endswith(".tif"):
            raise ValueError(f"Expected .tif file path, got {key}")
        return GDALPath(self.s3_prefix + "/" + key.removesuffix(".tif") + "_cog.tif")

    def get_dem_key(self) -> GDALPath:
        """GDAL virtual file system path to the BC DEM raster."""
        return GDALPath(f"{self.s3_prefix}/sfms/static/bc_elevation.tif")

    def get_mask_key(self) -> GDALPath:
        """GDAL virtual file system path to the BC boundary mask raster."""
        return GDALPath(f"{self.s3_prefix}/sfms/static/bc_mask.tif")

    def get_fuel_raster_key(self, datetime_utc: datetime, version: int) -> S3Key:
        """S3 key for a versioned fuel type raster."""
        assert_all_utc(datetime_utc)
        year = datetime_utc.year
        return S3Key(f"sfms/static/fuel/{year}/fbp{year}_v{version}.tif")

    def get_unprocessed_fuel_raster_key(self, object_name: str) -> S3Key:
        """S3 key for an unprocessed fuel raster staged at sfms/static/."""
        return S3Key(f"sfms/static/{object_name}")
