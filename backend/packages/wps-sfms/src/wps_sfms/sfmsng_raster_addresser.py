"""
Raster key addresser for the WPS fire weather processing pipeline.

Uses a `sfms_ng/` S3 root prefix, completely separate from the legacy
`sfms/` storage used by RasterKeyAddresser.
"""

from datetime import datetime, timedelta

from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import (
    BaseRasterAddresser,
    FBPParameter,
    FWIParameter,
    GDALPath,
    S3Key,
    SFMSInterpolatedWeatherParameter,
)
from wps_shared.utils.time import assert_all_utc

from wps_sfms.raster_inputs import FWIInputs, SurfaceFuelConsumptionInputs


class SFMSNGRasterAddresser(BaseRasterAddresser):
    """
    Raster key addresser for the new SFMS processing pipeline.

    All dynamic raster outputs are stored under the `sfms_ng/` root prefix,
    keeping them fully separate from the legacy SFMS storage at `sfms/`.
    """

    def __init__(self):
        super().__init__()
        self.root = "sfms_ng"

    def get_weather_key(
        self,
        datetime_utc: datetime,
        weather_param: SFMSInterpolatedWeatherParameter,
        run_type: RunType,
    ) -> S3Key:
        """
        S3 key for an interpolated weather parameter raster.

        Format: sfms_ng/{run_type}/YYYY/MM/DD/{param}_YYYYMMDD.tif
        """
        assert_all_utc(datetime_utc)
        date = datetime_utc.date()
        param = weather_param.value
        date_str = date.isoformat().replace("-", "")
        return S3Key(
            f"{self.root}/{run_type.value}/{date.year:04d}/{date.month:02d}/{date.day:02d}/{param}_{date_str}.tif"
        )

    def get_actual_weather_key(
        self, datetime_utc: datetime, weather_param: SFMSInterpolatedWeatherParameter
    ) -> S3Key:
        """Compatibility wrapper for actual weather raster keys."""
        return self.get_weather_key(datetime_utc, weather_param, RunType.ACTUAL)

    def get_forecast_weather_key(
        self, datetime_utc: datetime, weather_param: SFMSInterpolatedWeatherParameter
    ) -> S3Key:
        """Compatibility wrapper for forecast weather raster keys."""
        return self.get_weather_key(datetime_utc, weather_param, RunType.FORECAST)

    def get_index_key(
        self, datetime_utc: datetime, fwi_param: FWIParameter, run_type: RunType
    ) -> S3Key:
        """
        S3 key for an FWI index raster output.

        Format: sfms_ng/{run_type}/YYYY/MM/DD/{param}_YYYYMMDD.tif
        """
        assert_all_utc(datetime_utc)
        date = datetime_utc.date()
        date_str = date.isoformat().replace("-", "")
        return S3Key(
            f"{self.root}/{run_type.value}/{date.year:04d}/{date.month:02d}/{date.day:02d}/{fwi_param.value}_{date_str}.tif"
        )

    def get_actual_index_key(self, datetime_utc: datetime, fwi_param: FWIParameter) -> S3Key:
        """Compatibility wrapper for actual FWI index raster keys."""
        return self.get_index_key(datetime_utc, fwi_param, RunType.ACTUAL)

    def get_forecast_index_key(self, datetime_utc: datetime, fwi_param: FWIParameter) -> S3Key:
        """Compatibility wrapper for forecast FWI index raster keys."""
        return self.get_index_key(datetime_utc, fwi_param, RunType.FORECAST)

    def get_fbp_key(
        self, datetime_utc: datetime, fbp_param: FBPParameter, run_type: RunType
    ) -> S3Key:
        """S3 key for a calculated FBP parameter raster."""
        assert_all_utc(datetime_utc)
        date = datetime_utc.date()
        date_str = date.isoformat().replace("-", "")
        return S3Key(
            f"{self.root}/{run_type.value}/{date.year:04d}/{date.month:02d}/{date.day:02d}/"
            f"{fbp_param.value}_{date_str}.tif"
        )

    def get_surface_fuel_consumption_inputs(
        self,
        datetime_to_process: datetime,
        run_type: RunType,
        fuel_key: GDALPath,
        percent_conifer_key: GDALPath,
    ) -> SurfaceFuelConsumptionInputs:
        """Build the raster dependencies for same-day SFC."""
        assert_all_utc(datetime_to_process)
        return SurfaceFuelConsumptionInputs(
            fuel_key=fuel_key,
            mask_key=self.get_mask_key(),
            ffmc_key=self.gdal_path(
                self.get_index_key(datetime_to_process, FWIParameter.FFMC, run_type)
            ),
            bui_key=self.gdal_path(
                self.get_index_key(datetime_to_process, FWIParameter.BUI, run_type)
            ),
            percent_conifer_key=percent_conifer_key,
            output_key=self.get_fbp_key(datetime_to_process, FBPParameter.SFC, run_type),
            run_type=run_type,
        )

    def get_fwi_inputs(
        self,
        datetime_to_process: datetime,
        fwi_param: FWIParameter,
        run_type: RunType,
        previous_base_run_type: RunType | None = None,
    ) -> FWIInputs:
        """
        Build FWIInputs for one index calculation.

        Dependency keys vary by requested index:
        - FFMC, DMC, DC: yesterday's same index using previous_base_run_type
        - ISI: same-day FFMC for run_type + same-day wind speed
        - BUI: same-day DMC/DC for run_type
        - FWI: same-day ISI/BUI for run_type

        :param datetime_to_process: UTC datetime being processed
        :param fwi_param: Which FWI parameter to calculate
        :param run_type: Run type for same-day weather and output keys
        :param previous_base_run_type: Run type for previous-day FFMC/DMC/DC seeds
        :return: FWIInputs ready for FWIProcessor
        """
        assert_all_utc(datetime_to_process)
        yesterday = datetime_to_process - timedelta(days=1)
        base_run_type = previous_base_run_type or run_type

        weather_keys = {
            param: self.gdal_path(self.get_weather_key(datetime_to_process, param, run_type))
            for param in (
                SFMSInterpolatedWeatherParameter.TEMP,
                SFMSInterpolatedWeatherParameter.RH,
                SFMSInterpolatedWeatherParameter.PRECIP,
                SFMSInterpolatedWeatherParameter.WIND_SPEED,
            )
        }

        if fwi_param in (FWIParameter.FFMC, FWIParameter.DMC, FWIParameter.DC):
            index_keys = {
                fwi_param: self.gdal_path(self.get_index_key(yesterday, fwi_param, base_run_type))
            }
        elif fwi_param == FWIParameter.ISI:
            index_keys = {
                FWIParameter.FFMC: self.gdal_path(
                    self.get_index_key(datetime_to_process, FWIParameter.FFMC, run_type)
                )
            }
        elif fwi_param == FWIParameter.BUI:
            index_keys = {
                FWIParameter.DMC: self.gdal_path(
                    self.get_index_key(datetime_to_process, FWIParameter.DMC, run_type)
                ),
                FWIParameter.DC: self.gdal_path(
                    self.get_index_key(datetime_to_process, FWIParameter.DC, run_type)
                ),
            }
        elif fwi_param == FWIParameter.FWI:
            index_keys = {
                FWIParameter.ISI: self.gdal_path(
                    self.get_index_key(datetime_to_process, FWIParameter.ISI, run_type)
                ),
                FWIParameter.BUI: self.gdal_path(
                    self.get_index_key(datetime_to_process, FWIParameter.BUI, run_type)
                ),
            }
        else:
            raise ValueError(f"Unsupported FWI parameter: {fwi_param.value}")

        output_key = self.get_index_key(datetime_to_process, fwi_param, run_type)
        return FWIInputs(
            weather_keys=weather_keys,
            index_keys=index_keys,
            output_key=output_key,
            run_type=run_type,
        )

    def get_actual_fwi_inputs(
        self, datetime_to_process: datetime, fwi_param: FWIParameter
    ) -> FWIInputs:
        """Compatibility wrapper for actual-run FWI inputs."""
        return self.get_fwi_inputs(datetime_to_process, fwi_param, RunType.ACTUAL)

    def get_forecast_fwi_inputs(
        self,
        datetime_to_process: datetime,
        fwi_param: FWIParameter,
        previous_base_run_type: RunType = RunType.FORECAST,
    ) -> FWIInputs:
        """Compatibility wrapper for forecast-run FWI inputs."""
        return self.get_fwi_inputs(
            datetime_to_process,
            fwi_param,
            RunType.FORECAST,
            previous_base_run_type=previous_base_run_type,
        )
