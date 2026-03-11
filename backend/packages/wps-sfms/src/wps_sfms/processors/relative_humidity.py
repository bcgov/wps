import logging
import numpy as np
from osgeo import gdal
from wps_sfms.interpolation.field import (
    DEW_POINT_LAPSE_RATE,
    ScalarField,
    compute_adjusted_values,
    compute_rh,
)
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_sfms.interpolation.common import (
    SFMS_NO_DATA,
    log_interpolation_stats,
)
from wps_sfms.interpolation.grid import build_grid_context
from wps_sfms.processors.idw import RasterProcessor, idw_on_valid_pixels

logger = logging.getLogger(__name__)


class RHInterpolator(RasterProcessor):
    """Interpolates RH via dew point IDW + elevation adjustment.

    Requires that temperature interpolation has already been run for this date,
    as it reads the interpolated temperature raster from S3.
    """

    def __init__(
        self,
        mask_path: str,
        dem_path: str,
        temp_raster_path: str,
        field: ScalarField,
    ):
        super().__init__(mask_path)
        self.dem_path = dem_path
        self.temp_raster_path = temp_raster_path
        self.field = field

    def interpolate(self, reference_raster_path: str) -> WPSDataset:
        grid = build_grid_context(
            reference_raster_path,
            self.mask_path,
            dem_path=self.dem_path,
            temperature_raster_path=self.temp_raster_path,
        )
        assert grid.valid_dem_values is not None
        assert grid.temperature_data is not None

        rh_array = np.full((grid.y_size, grid.x_size), SFMS_NO_DATA, dtype=np.float32)

        logger.info(
            "Interpolating dew point for RH raster grid (%d x %d)", grid.x_size, grid.y_size
        )

        idw_result = idw_on_valid_pixels(
            valid_lats=grid.valid_lats,
            valid_lons=grid.valid_lons,
            valid_yi=grid.valid_yi,
            valid_xi=grid.valid_xi,
            station_lats=self.field.lats,
            station_lons=self.field.lons,
            station_values=self.field.values,
            total_pixels=grid.total_pixels,
            label="dew point",
        )

        sea = idw_result.values
        elev = grid.valid_dem_values[idw_result.succeeded_mask].astype(np.float32, copy=False)
        adjusted_dewpoints = compute_adjusted_values(sea, elev, DEW_POINT_LAPSE_RATE)

        rh_values = compute_rh(
            grid.temperature_data[idw_result.rows, idw_result.cols],
            adjusted_dewpoints,
        )
        rh_array[idw_result.rows, idw_result.cols] = rh_values

        log_interpolation_stats(
            idw_result.total_pixels,
            idw_result.interpolated_count,
            idw_result.failed_interpolation_count,
            idw_result.skipped_nodata_count,
        )

        if idw_result.interpolated_count == 0:
            raise RuntimeError(
                f"No pixels were successfully interpolated from {len(self.field.lats)} station(s). "
                "Check that station coordinates fall within the raster extent and that at least "
                "one station has a valid dew point value."
            )

        return WPSDataset.from_array(
            array=rh_array,
            geotransform=grid.geotransform,
            projection=grid.projection,
            nodata_value=SFMS_NO_DATA,
            datatype=gdal.GDT_Float32,
        )
