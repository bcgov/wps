from datetime import date
import numpy as np
from app.auto_spatial_advisory.run_type import RunType
from app.utils.s3 import get_client
from app import config
from app.utils.geospatial import GeospatialOptions, Vector2RasterOptions, read_raster_into_memory


async def summarize_advisory_area_by_tpi(forecast_or_actual: RunType, for_date: date):
    """
    Masks classified HFI against classified TPI and counts frequency of TPI classes with classified HFI pixels.

    :return: Mapping of TPI class to HFI pixel count
    """
    pmtiles_filename = f'hfi{for_date.strftime("%Y%m%d")}.pmtiles'
    iso_date = for_date.isoformat()

    async with get_client() as (client, bucket):
        tpi_result = await read_raster_into_memory(
            client,
            bucket,
            f'dem/tpi/{config.get("CLASSIFIED_TPI_DEM_NAME")}',
            GeospatialOptions(include_geotransform=True, include_projection=True, include_x_size=True, include_y_size=True),
        )
        hfi_result = await read_raster_into_memory(
            client,
            bucket,
            f"psu/pmtiles/hfi/{forecast_or_actual.value}/{iso_date}/{pmtiles_filename}",
            GeospatialOptions(
                vector_options=Vector2RasterOptions(
                    source_geotransform=tpi_result.data_geotransform,
                    source_projection=tpi_result.data_projection,
                    source_x_size=tpi_result.data_x_size,
                    source_y_size=tpi_result.data_y_size,
                )
            ),
        )
        # transforms all pixels that are 255 to 1, this is what we get from pmtiles
        hfi_4k_or_above = np.where(hfi_result.data_array == 255, 1, hfi_result.data_array)
        hfi_masked_tpi = np.multiply(tpi_result.data_array, hfi_4k_or_above)
        # Get unique values and their counts
        tpi_classes, counts = np.unique(hfi_masked_tpi, return_counts=True)
        tpi_class_freq_dist = dict(zip(tpi_classes, counts))

        return tpi_class_freq_dist
