import enum
from dataclasses import dataclass
from datetime import datetime

from wps_shared import config
from wps_shared.run_type import RunType
from wps_shared.utils.time import assert_all_utc


class SFMSInterpolatedWeatherParameter(enum.Enum):
    TEMP = "temp"
    RH = "rh"
    WIND_SPEED = "wind_speed"
    PRECIP = "precip"


class FWIParameter(enum.Enum):
    DC = "dc"
    DMC = "dmc"
    BUI = "bui"
    FFMC = "ffmc"
    ISI = "isi"
    FWI = "fwi"


@dataclass(frozen=True)
class FWIInputs:
    """All S3 keys and metadata needed for a single FWI index calculation."""

    temp_key: str
    rh_key: str
    precip_key: str
    prev_fwi_key: str
    output_key: str
    cog_key: str  # GDAL-prefixed path for COG output
    run_type: RunType


class BaseRasterAddresser:
    """S3/GDAL utilities shared across raster key addressers."""

    def __init__(self):
        self.s3_prefix = f"/vsis3/{config.get('OBJECT_STORE_BUCKET')}"

    def gdal_path(self, key: str) -> str:
        """Return a GDAL vsis3-prefixed path for a plain S3 key."""
        return f"{self.s3_prefix}/{key}"

    def gdal_prefix_keys(self, *keys):
        """Prefix keys with vsis3/{bucket} for reading from S3 with GDAL."""
        return tuple(self.gdal_path(key) for key in keys)

    def get_cog_key(self, key: str) -> str:
        """Given a .tif key, return a GDAL-prefixed _cog.tif path."""
        if not key.endswith(".tif"):
            raise ValueError(f"Expected .tif file path, got {key}")
        return self.s3_prefix + "/" + key.removesuffix(".tif") + "_cog.tif"

    def get_dem_key(self) -> str:
        """GDAL virtual file system path to the BC DEM raster."""
        return f"{self.s3_prefix}/sfms/static/bc_elevation.tif"

    def get_mask_key(self) -> str:
        """GDAL virtual file system path to the BC boundary mask raster."""
        return f"{self.s3_prefix}/sfms/static/bc_mask.tif"

    def get_fuel_raster_key(self, datetime_utc: datetime, version: int) -> str:
        """S3 key for a versioned fuel type raster."""
        assert_all_utc(datetime_utc)
        year = datetime_utc.year
        return f"sfms/static/fuel/{year}/fbp{year}_v{version}.tif"

    def get_unprocessed_fuel_raster_key(self, object_name: str) -> str:
        """S3 key for an unprocessed fuel raster staged at sfms/static/."""
        return f"sfms/static/{object_name}"
