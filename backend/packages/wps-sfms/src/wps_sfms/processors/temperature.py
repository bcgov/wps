import logging
import numpy as np
from osgeo import gdal
from wps_sfms.interpolation.source import LAPSE_RATE, StationTemperatureSource
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_sfms.interpolation.common import SFMS_NO_DATA, log_interpolation_stats
from wps_sfms.processors.idw import BaseInterpolator, idw_on_valid_pixels

logger = logging.getLogger(__name__)


class TemperatureInterpolator(BaseInterpolator[StationTemperatureSource]):
    """Interpolates station temperatures using IDW with elevation adjustment.

    Uses ``BaseInterpolator[StationTemperatureSource]``; the source contract is
    ``get_interpolation_data() -> (lats, lons, sea_level_temps)``.
    """

    def __init__(self, mask_path: str, dem_path: str):
        super().__init__(mask_path)
        self.dem_path = dem_path

    def interpolate(
        self, source: StationTemperatureSource, reference_raster_path: str
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

            with WPSDataset(self.dem_path) as dem_ds:
                dem_band: gdal.Band = dem_ds.ds.GetRasterBand(1)
                dem_data = dem_band.ReadAsArray()
                if dem_data is None:
                    raise ValueError("Failed to read DEM data")

                temp_array = np.full((y_size, x_size), SFMS_NO_DATA, dtype=np.float32)

                with WPSDataset(self.mask_path) as mask_ds:
                    valid_mask = ref_ds.apply_mask(mask_ds.warp_to_match(ref_ds))

                lats, lons, valid_yi, valid_xi = dem_ds.get_lat_lon_coords(valid_mask)
                valid_elevations = dem_data[valid_mask]

                total_pixels = x_size * y_size

                logger.info("Interpolating temperature for raster grid (%d x %d)", x_size, y_size)

                station_lats, station_lons, sea_level_temps = source.get_interpolation_data()
                idw_result = idw_on_valid_pixels(
                    valid_lats=lats,
                    valid_lons=lons,
                    valid_yi=valid_yi,
                    valid_xi=valid_xi,
                    station_lats=station_lats,
                    station_lons=station_lons,
                    station_values=sea_level_temps,
                    total_pixels=total_pixels,
                    label="temperature",
                )

                sea = idw_result.values
                elev = valid_elevations[idw_result.succeeded_mask].astype(np.float32, copy=False)
                actual_temps = source.compute_adjusted_values(sea, elev, LAPSE_RATE)
                temp_array[idw_result.rows, idw_result.cols] = actual_temps

            log_interpolation_stats(
                idw_result.total_pixels,
                idw_result.interpolated_count,
                idw_result.failed_interpolation_count,
                idw_result.skipped_nodata_count,
            )

            if idw_result.interpolated_count == 0:
                raise RuntimeError(
                    f"No pixels were successfully interpolated from {len(station_lats)} station(s). "
                    "Check that station coordinates fall within the raster extent and that at least "
                    "one station has a valid temperature value."
                )

            return WPSDataset.from_array(
                array=temp_array,
                geotransform=geo_transform,
                projection=projection,
                nodata_value=SFMS_NO_DATA,
                datatype=gdal.GDT_Float32,
            )
