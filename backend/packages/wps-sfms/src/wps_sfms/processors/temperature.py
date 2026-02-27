from wps_sfms.interpolation.source import StationTemperatureSource
from wps_sfms.interpolation.temperature import interpolate_temperature_to_raster
from wps_sfms.processors.idw import InterpolationProcessor


class TemperatureInterpolationProcessor(InterpolationProcessor):
    """Processor for interpolating station temperatures using IDW with elevation adjustment."""

    def __init__(self, mask_path: str, dem_path: str):
        super().__init__(mask_path)
        self.dem_path = dem_path

    def _interpolate(
        self, source: StationTemperatureSource, reference_raster_path: str, output_path: str
    ) -> None:
        interpolate_temperature_to_raster(
            source, reference_raster_path, self.dem_path, output_path, self.mask_path
        )
