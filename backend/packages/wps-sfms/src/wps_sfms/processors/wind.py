import logging

import numpy as np
from osgeo import gdal

from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_sfms.interpolation.common import SFMS_NO_DATA, log_interpolation_stats
from wps_sfms.interpolation.source import StationWindVectorSource
from wps_sfms.processors.idw import Interpolator, idw_on_valid_pixels

logger = logging.getLogger(__name__)


class WindSpeedInterpolator(Interpolator):
    """Interpolates wind speed using base IDW workflow."""


class WindDirectionInterpolator(Interpolator):
    """Interpolates wind direction by IDW on u/v components then reconstructing direction."""

    @staticmethod
    def compute_direction_from_uv(u: np.ndarray, v: np.ndarray) -> np.ndarray:
        """Match legacy SFMS direction reconstruction from interpolated u/v."""
        u = np.asarray(u, dtype=np.float32)
        v = np.asarray(v, dtype=np.float32)
        direction = np.zeros(u.shape, dtype=np.float32)

        zero_v = np.abs(v) < np.float32(1e-6)
        nonzero_v = ~zero_v

        direction[nonzero_v] = (
            np.degrees(np.arctan2(u[nonzero_v], v[nonzero_v])) + np.float32(180.0)
        ).astype(np.float32)

        zero_u = np.abs(u) < np.float32(1e-6)

        direction[zero_v & (u < 0.0)] = 90.0
        direction[zero_v & (u > 0.0)] = 270.0
        direction[zero_v & zero_u] = 0.0
        return direction

    def interpolate(
        self, source: StationWindVectorSource, reference_raster_path: str
    ) -> WPSDataset:
        with WPSDataset(reference_raster_path) as ref_ds:
            geo_transform = ref_ds.ds.GetGeoTransform()
            if geo_transform is None:
                raise ValueError(
                    f"Failed to get geotransform from reference raster: {reference_raster_path}"
                )
            projection = ref_ds.ds.GetProjection()
            x_size = ref_ds.ds.RasterXSize
            y_size = ref_ds.ds.RasterYSize

            wind_direction_array = np.full((y_size, x_size), SFMS_NO_DATA, dtype=np.float32)

            with WPSDataset(self.mask_path) as mask_ds:
                valid_mask = ref_ds.apply_mask(mask_ds.warp_to_match(ref_ds))

            lats, lons, valid_yi, valid_xi = ref_ds.get_lat_lon_coords(valid_mask)
            total_pixels = x_size * y_size

            logger.info("Interpolating wind direction for raster grid (%d x %d)", x_size, y_size)

            station_lats, station_lons, station_u, station_v = source.get_uv_interpolation_data()

            u_result = idw_on_valid_pixels(
                valid_lats=lats,
                valid_lons=lons,
                valid_yi=valid_yi,
                valid_xi=valid_xi,
                station_lats=station_lats,
                station_lons=station_lons,
                station_values=station_u,
                total_pixels=total_pixels,
                label="wind-u component",
            )
            v_result = idw_on_valid_pixels(
                valid_lats=lats,
                valid_lons=lons,
                valid_yi=valid_yi,
                valid_xi=valid_xi,
                station_lats=station_lats,
                station_lons=station_lons,
                station_values=station_v,
                total_pixels=total_pixels,
                label="wind-v component",
            )

            wind_success = u_result.succeeded_mask & v_result.succeeded_mask
            interpolated_count = int(np.sum(wind_success))
            failed_interpolation_count = len(wind_success) - interpolated_count

            if interpolated_count > 0:
                rows = valid_yi[wind_success]
                cols = valid_xi[wind_success]
                directions = self.compute_direction_from_uv(
                    u_result.interpolated_values[wind_success],
                    v_result.interpolated_values[wind_success],
                )
                wind_direction_array[rows, cols] = directions

            log_interpolation_stats(
                total_pixels=total_pixels,
                interpolated_count=interpolated_count,
                failed_interpolation_count=failed_interpolation_count,
                skipped_nodata_count=u_result.skipped_nodata_count,
            )

            if interpolated_count == 0:
                raise RuntimeError(
                    f"No pixels were successfully interpolated from {len(station_lats)} station(s). "
                    "Check that station coordinates fall within the raster extent and that at least "
                    "one station has both a valid wind speed and wind direction value."
                )

            return WPSDataset.from_array(
                array=wind_direction_array,
                geotransform=geo_transform,
                projection=projection,
                nodata_value=SFMS_NO_DATA,
                datatype=gdal.GDT_Float32,
            )
