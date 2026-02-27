from wps_sfms.interpolation.relative_humidity import interpolate_rh_to_raster
from wps_sfms.interpolation.source import StationDewPointSource
from wps_sfms.processors.idw import InterpolationProcessor


class RHInterpolationProcessor(InterpolationProcessor):
    """Processor for interpolating RH via dew point IDW + elevation adjustment.

    Requires that temperature interpolation has already been run for this date,
    as it reads the interpolated temperature raster from S3.
    """

    def __init__(self, mask_path: str, dem_path: str, temp_raster_path: str):
        super().__init__(mask_path)
        self.dem_path = dem_path
        self.temp_raster_path = temp_raster_path

    def _interpolate(
        self, source: StationDewPointSource, reference_raster_path: str, output_path: str
    ) -> None:
        interpolate_rh_to_raster(
            source,
            self.temp_raster_path,
            reference_raster_path,
            self.dem_path,
            output_path,
            self.mask_path,
        )
