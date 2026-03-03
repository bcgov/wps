"""
Raster key addresser for the WPS fire weather processing pipeline.

Uses a `sfms_ng/` S3 root prefix, completely separate from the legacy
`sfms/` storage used by RasterKeyAddresser.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Mapping

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
    """All input key mappings and metadata needed for a single FWI calculation.

    `weather_keys` and `index_keys` values are GDALPath values (/vsis3/...) for
    reading via GDAL. `output_key` is a plain S3Key for writing via boto3.
    """

    weather_keys: Mapping[SFMSInterpolatedWeatherParameter, GDALPath]
    index_keys: Mapping[FWIParameter, GDALPath]
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
        return S3Key(
            f"{self.root}/actual/{date.year:04d}/{date.month:02d}/{date.day:02d}/{param}_{date_str}.tif"
        )

    def get_actual_index_key(self, datetime_utc: datetime, fwi_param: FWIParameter) -> S3Key:
        """
        S3 key for an actual FWI index raster output.

        Format: sfms_ng/actual/YYYY/MM/DD/{param}_YYYYMMDD.tif
        """
        assert_all_utc(datetime_utc)
        date = datetime_utc.date()
        date_str = date.isoformat().replace("-", "")
        return S3Key(
            f"{self.root}/actual/{date.year:04d}/{date.month:02d}/{date.day:02d}/{fwi_param.value}_{date_str}.tif"
        )

    def get_actual_fwi_inputs(
        self, datetime_to_process: datetime, fwi_param: FWIParameter
    ) -> FWIInputs:
        """
        Build FWIInputs for one actual-run index calculation.

        Dependency keys vary by requested index:
        - FFMC, DMC, DC: yesterday's same index + today's weather
        - ISI: today's FFMC + today's wind speed
        - BUI: today's DMC + today's DC
        - FWI: today's ISI + today's BUI

        :param datetime_to_process: UTC datetime being processed
        :param fwi_param: Which FWI parameter to calculate
        :return: FWIInputs ready for FWIProcessor
        """
        assert_all_utc(datetime_to_process)
        yesterday = datetime_to_process - timedelta(days=1)

        weather_keys = {
            param: self.gdal_path(self.get_actual_weather_key(datetime_to_process, param))
            for param in (
                SFMSInterpolatedWeatherParameter.TEMP,
                SFMSInterpolatedWeatherParameter.RH,
                SFMSInterpolatedWeatherParameter.PRECIP,
                SFMSInterpolatedWeatherParameter.WIND_SPEED,
            )
        }

        if fwi_param in (FWIParameter.FFMC, FWIParameter.DMC, FWIParameter.DC):
            index_keys = {
                fwi_param: self.gdal_path(self.get_actual_index_key(yesterday, fwi_param))
            }
        elif fwi_param == FWIParameter.ISI:
            index_keys = {
                FWIParameter.FFMC: self.gdal_path(
                    self.get_actual_index_key(datetime_to_process, FWIParameter.FFMC)
                )
            }
        elif fwi_param == FWIParameter.BUI:
            index_keys = {
                FWIParameter.DMC: self.gdal_path(
                    self.get_actual_index_key(datetime_to_process, FWIParameter.DMC)
                ),
                FWIParameter.DC: self.gdal_path(
                    self.get_actual_index_key(datetime_to_process, FWIParameter.DC)
                ),
            }
        elif fwi_param == FWIParameter.FWI:
            index_keys = {
                FWIParameter.ISI: self.gdal_path(
                    self.get_actual_index_key(datetime_to_process, FWIParameter.ISI)
                ),
                FWIParameter.BUI: self.gdal_path(
                    self.get_actual_index_key(datetime_to_process, FWIParameter.BUI)
                ),
            }
        else:
            raise ValueError(f"Unsupported FWI parameter: {fwi_param.value}")

        output_key = self.get_actual_index_key(datetime_to_process, fwi_param)
        return FWIInputs(
            weather_keys=weather_keys,
            index_keys=index_keys,
            output_key=output_key,
            cog_key=self.get_cog_key(output_key),
            run_type=RunType.ACTUAL,
        )
