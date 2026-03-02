"""
Raster key addresser for the WPS fire weather processing pipeline.

Uses a `sfms_ng/` S3 root prefix, completely separate from the legacy
`sfms/` storage used by RasterKeyAddresser.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import (
    BaseRasterAddresser,
    FWIParameter,
    GDALPath,
    S3Key,
    SFMSInterpolatedWeatherParameter,
)
from wps_shared.utils.time import assert_all_utc


@dataclass(frozen=True)
class FWIInputs:
    """All S3 keys and metadata needed for a single FWI index calculation.

    Input keys (temp_key, rh_key, precip_key, prev_fwi_key, cog_key) are
    GDALPath values (/vsis3/...) for reading via GDAL. output_key is a plain
    S3Key for writing via boto3.
    """

    temp_key: GDALPath
    rh_key: GDALPath
    precip_key: GDALPath
    prev_fwi_key: GDALPath
    output_key: S3Key
    cog_key: GDALPath
    run_type: RunType


class SFMSNGRasterAddresser(BaseRasterAddresser):
    """
    Raster key addresser for the new SFMS processing pipeline.

    All dynamic raster outputs are stored under the `sfms_ng/` root prefix,
    keeping them fully separate from the legacy SFMS storage at `sfms/`.
    """

    def __init__(self):
        super().__init__()
        self.root = "sfms_ng"

    def get_actual_weather_key(
        self, datetime_utc: datetime, weather_param: SFMSInterpolatedWeatherParameter
    ) -> S3Key:
        """
        S3 key for an interpolated weather parameter raster.

        Format: sfms_ng/actual/YYYY/MM/DD/{param}_YYYYMMDD.tif
        """
        assert_all_utc(datetime_utc)
        date = datetime_utc.date()
        param = weather_param.value
        date_str = date.isoformat().replace("-", "")
        return S3Key(f"{self.root}/actual/{date.year:04d}/{date.month:02d}/{date.day:02d}/{param}_{date_str}.tif")

    def get_actual_index_key(self, datetime_utc: datetime, fwi_param: FWIParameter) -> S3Key:
        """
        S3 key for an actual FWI index raster output.

        Format: sfms_ng/actual/YYYY/MM/DD/{param}_YYYYMMDD.tif
        """
        assert_all_utc(datetime_utc)
        date = datetime_utc.date()
        date_str = date.isoformat().replace("-", "")
        return S3Key(f"{self.root}/actual/{date.year:04d}/{date.month:02d}/{date.day:02d}/{fwi_param.value}_{date_str}.tif")

    def get_actual_fwi_inputs(
        self, datetime_to_process: datetime, fwi_param: FWIParameter
    ) -> FWIInputs:
        """
        Build a FWIInputs for a station-interpolated actual run.

        Uses yesterday's uploaded FWI value as seed and today's interpolated
        weather rasters (temp, rh, precip) as inputs.

        :param datetime_to_process: UTC datetime being processed
        :param fwi_param: Which FWI parameter to calculate (FFMC, DMC, or DC)
        :return: FWIInputs ready for FWIProcessor
        """
        assert_all_utc(datetime_to_process)
        yesterday = datetime_to_process - timedelta(days=1)
        temp_key, rh_key, precip_key, prev_fwi_key = self.gdal_prefix_keys(
            self.get_actual_weather_key(datetime_to_process, SFMSInterpolatedWeatherParameter.TEMP),
            self.get_actual_weather_key(datetime_to_process, SFMSInterpolatedWeatherParameter.RH),
            self.get_actual_weather_key(
                datetime_to_process, SFMSInterpolatedWeatherParameter.PRECIP
            ),
            self.get_actual_index_key(yesterday, fwi_param),
        )
        output_key = self.get_actual_index_key(datetime_to_process, fwi_param)
        return FWIInputs(
            temp_key=temp_key,
            rh_key=rh_key,
            precip_key=precip_key,
            prev_fwi_key=prev_fwi_key,
            output_key=output_key,
            cog_key=self.get_cog_key(output_key),
            run_type=RunType.ACTUAL,
        )
