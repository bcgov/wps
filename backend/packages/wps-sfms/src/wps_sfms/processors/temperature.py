import logging
import numpy as np
from osgeo import gdal
from wps_sfms.interpolation.source import LAPSE_RATE, StationTemperatureSource
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import idw_interpolation
from wps_sfms.interpolation.common import SFMS_NO_DATA, log_interpolation_stats
from wps_sfms.processors.idw import Interpolator

logger = logging.getLogger(__name__)


class TemperatureInterpolator(Interpolator):
    """Interpolates station temperatures using IDW with elevation adjustment."""

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
                skipped_nodata_count = total_pixels - len(valid_yi)

                logger.info("Interpolating temperature for raster grid (%d x %d)", x_size, y_size)
                logger.info(
                    "Processing %d valid pixels (skipping %d NoData pixels)",
                    len(valid_yi),
                    skipped_nodata_count,
                )

                station_lats, station_lons, sea_level_temps = source.get_interpolation_data()
                logger.info(
                    "Running batch temperature IDW interpolation for %d pixels and %d stations",
                    len(lats),
                    len(station_lats),
                )

                interpolated_sea_level_temps = idw_interpolation(
                    lats, lons, station_lats, station_lons, sea_level_temps
                )
                assert isinstance(interpolated_sea_level_temps, np.ndarray)

                interpolation_succeeded = ~np.isnan(interpolated_sea_level_temps)
                interpolated_count = int(np.sum(interpolation_succeeded))
                failed_interpolation_count = len(interpolated_sea_level_temps) - interpolated_count

                rows = valid_yi[interpolation_succeeded]
                cols = valid_xi[interpolation_succeeded]

                sea = interpolated_sea_level_temps[interpolation_succeeded].astype(
                    np.float32, copy=False
                )
                elev = valid_elevations[interpolation_succeeded].astype(np.float32, copy=False)

                actual_temps = source.compute_adjusted_values(sea, elev, LAPSE_RATE)
                temp_array[rows, cols] = actual_temps

            log_interpolation_stats(
                total_pixels, interpolated_count, failed_interpolation_count, skipped_nodata_count
            )

            return WPSDataset.from_array(
                array=temp_array,
                geotransform=geo_transform,
                projection=projection,
                nodata_value=SFMS_NO_DATA,
                datatype=gdal.GDT_Float32,
            )
