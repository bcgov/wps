"""
Raster key addresser for the WPS fire weather processing pipeline.

Uses a `sfms_ng/` S3 root prefix, completely separate from the legacy
`sfms/` storage used by RasterKeyAddresser.
"""

from datetime import datetime, timedelta

from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import (
    BaseRasterAddresser,
    FWIInputs,
    FWIParameter,
    SFMSInterpolatedWeatherParameter,
)
from wps_shared.utils.time import assert_all_utc


class SFMSNGRasterAddresser(BaseRasterAddresser):
    """
    Raster key addresser for the new SFMS processing pipeline.

    All dynamic raster outputs are stored under the `sfms_ng/` root prefix,
    keeping them fully separate from the legacy SFMS storage at `sfms/`.
    """

    def __init__(self):
        super().__init__()
        self.root = "sfms_ng"

    def get_interpolated_key(self, datetime_utc: datetime, weather_param: SFMSInterpolatedWeatherParameter) -> str:
        """
        S3 key for an interpolated weather parameter raster.

        Format: sfms_ng/interpolated/{param}/YYYY/MM/DD/{param}_YYYYMMDD.tif
        """
        assert_all_utc(datetime_utc)
        date = datetime_utc.date()
        param = weather_param.value
        date_str = date.isoformat().replace("-", "")
        return f"{self.root}/interpolated/{param}/{date.year:04d}/{date.month:02d}/{date.day:02d}/{param}_{date_str}.tif"

    def get_uploaded_index_key(self, datetime_utc: datetime, fwi_param: FWIParameter) -> str:
        """
        S3 key for an uploaded FWI index raster (used as the previous-day seed).

        Format: sfms_ng/uploads/actual/YYYY-MM-DD/{param}YYYYMMDD.tif
        """
        assert_all_utc(datetime_utc)
        iso_date = datetime_utc.date().isoformat()
        return f"{self.root}/uploads/actual/{iso_date}/{fwi_param.value}{iso_date.replace('-', '')}.tif"

    def get_calculated_index_key(self, datetime_utc: datetime, fwi_param: FWIParameter, run_type: str = "actual") -> str:
        """
        S3 key for a calculated FWI index raster output.

        Format: sfms_ng/calculated/{run_type}/YYYY-MM-DD/{param}YYYYMMDD.tif
        """
        assert_all_utc(datetime_utc)
        iso_date = datetime_utc.date().isoformat()
        return f"{self.root}/calculated/{run_type}/{iso_date}/{fwi_param.value}{iso_date.replace('-', '')}.tif"

    def get_actual_fwi_inputs(self, datetime_to_process: datetime, fwi_param: FWIParameter) -> FWIInputs:
        """
        Build a FWIInputs for a station-interpolated actuals run.

        Uses yesterday's uploaded FWI value as seed and today's interpolated
        weather rasters (temp, rh, precip) as inputs.

        :param datetime_to_process: UTC datetime being processed
        :param fwi_param: Which FWI parameter to calculate (FFMC, DMC, or DC)
        :return: FWIInputs ready for FWIProcessor
        """
        assert_all_utc(datetime_to_process)
        yesterday = datetime_to_process - timedelta(days=1)
        temp_key, rh_key, precip_key, prev_fwi_key = self.gdal_prefix_keys(
            self.get_interpolated_key(datetime_to_process, SFMSInterpolatedWeatherParameter.TEMP),
            self.get_interpolated_key(datetime_to_process, SFMSInterpolatedWeatherParameter.RH),
            self.get_interpolated_key(datetime_to_process, SFMSInterpolatedWeatherParameter.PRECIP),
            self.get_uploaded_index_key(yesterday, fwi_param),
        )
        output_key = self.get_calculated_index_key(datetime_to_process, fwi_param, run_type=RunType.ACTUAL.value)
        return FWIInputs(
            temp_key=temp_key,
            rh_key=rh_key,
            precip_key=precip_key,
            prev_fwi_key=prev_fwi_key,
            output_key=output_key,
            cog_key=self.get_cog_key(output_key),
            run_type=RunType.ACTUAL,
        )
