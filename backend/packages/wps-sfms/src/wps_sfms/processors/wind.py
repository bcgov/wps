import logging

import numpy as np
from osgeo import gdal
from wps_shared.geospatial.wps_dataset import WPSDataset

from wps_sfms.interpolation.common import SFMS_NO_DATA, log_interpolation_stats
from wps_sfms.interpolation.fields import WindVectorField
from wps_sfms.interpolation.grid import build_grid_context
from wps_sfms.processors.idw import Interpolator, RasterProcessor, idw_on_valid_pixels

logger = logging.getLogger(__name__)


class WindSpeedInterpolator(Interpolator):
    """Interpolates wind speed using base IDW workflow."""


class WindDirectionInterpolator(RasterProcessor):
    """Interpolates wind direction by IDW on u/v components then reconstructing direction."""

    def __init__(self, mask_path: str, field: WindVectorField):
        super().__init__(mask_path)
        self.field = field

    @staticmethod
    def compute_direction_from_uv(u: np.ndarray, v: np.ndarray) -> np.ndarray:
        """
        Match legacy SFMS wind direction reconstruction from interpolated u/v.
        https://github.com/cffdrs/sfms/blob/main/src/SfmsWeather.cpp

        :param u: u component of wind vector
        :param v: v component of wind vector
        :return: wind direction in degrees
        """
        u = np.asarray(u, dtype=np.float32)
        v = np.asarray(v, dtype=np.float32)
        direction = np.zeros(u.shape, dtype=np.float32)

        zero_v = np.abs(v) < np.float32(1e-6)
        nonzero_v = ~zero_v

        direction[nonzero_v] = (
            np.degrees(np.arctan2(u[nonzero_v], v[nonzero_v])) + np.float32(180.0)
        ).astype(np.float32)

        zero_u = np.abs(u) < np.float32(1e-6)

        # when v is effectively zero, avoid unstable/ambiguous atan2 results by applying legacy
        # SFMS rules: u<0 => 90 deg, u>0 => 270 deg, and u~=0 & v~=0 (calm/no directional signal) => 0 deg.
        direction[zero_v & (u < 0.0)] = 90.0
        direction[zero_v & (u > 0.0)] = 270.0
        direction[zero_v & zero_u] = 0.0
        return direction

    def interpolate(self, reference_raster_path: str) -> WPSDataset:
        grid = build_grid_context(reference_raster_path, self.mask_path)
        wind_direction_array = np.full((grid.y_size, grid.x_size), SFMS_NO_DATA, dtype=np.float32)

        logger.info("Interpolating wind direction for raster grid (%d x %d)", grid.x_size, grid.y_size)

        u_result = idw_on_valid_pixels(
            valid_lats=grid.valid_lats,
            valid_lons=grid.valid_lons,
            valid_yi=grid.valid_yi,
            valid_xi=grid.valid_xi,
            station_lats=self.field.lats,
            station_lons=self.field.lons,
            station_values=self.field.u,
            total_pixels=grid.total_pixels,
            label="wind-u component",
        )
        v_result = idw_on_valid_pixels(
            valid_lats=grid.valid_lats,
            valid_lons=grid.valid_lons,
            valid_yi=grid.valid_yi,
            valid_xi=grid.valid_xi,
            station_lats=self.field.lats,
            station_lons=self.field.lons,
            station_values=self.field.v,
            total_pixels=grid.total_pixels,
            label="wind-v component",
        )

        wind_success = u_result.succeeded_mask & v_result.succeeded_mask
        interpolated_count = int(np.sum(wind_success))
        failed_interpolation_count = len(wind_success) - interpolated_count

        if interpolated_count > 0:
            rows = grid.valid_yi[wind_success]
            cols = grid.valid_xi[wind_success]
            directions = self.compute_direction_from_uv(
                u_result.interpolated_values[wind_success],
                v_result.interpolated_values[wind_success],
            )
            wind_direction_array[rows, cols] = directions

        log_interpolation_stats(
            total_pixels=grid.total_pixels,
            interpolated_count=interpolated_count,
            failed_interpolation_count=failed_interpolation_count,
            skipped_nodata_count=u_result.skipped_nodata_count,
        )

        if interpolated_count == 0:
            raise RuntimeError(
                f"No pixels were successfully interpolated from {len(self.field.lats)} station(s). "
                "Check that station coordinates fall within the raster extent and that at least "
                "one station has both a valid wind speed and wind direction value."
            )

        return WPSDataset.from_array(
            array=wind_direction_array,
            geotransform=grid.geotransform,
            projection=grid.projection,
            nodata_value=SFMS_NO_DATA,
            datatype=gdal.GDT_Float32,
        )
