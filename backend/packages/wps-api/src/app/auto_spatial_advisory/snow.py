import logging
import os

import numpy as np
from osgeo import gdal
from wps_shared import config
from wps_shared.db.models.snow import ProcessedSnow
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.utils.s3 import gdal_s3_context

MASKED_HFI_PATH_NAME = "masked_hfi.tif"

logger = logging.getLogger(__name__)


def classify_snow_mask(snow_source: WPSDataset) -> WPSDataset:
    """
    Given snow coverage data, re-classify the data to act as a mask for future HFI processing.
    A NDSI (ie. snow coverage) value between 0-100 represent snow coverage. Here we define snow coverage
    between 10-100. We need to consult the literature or data scientists on proper use of NDSI.
    """
    # In the classified data 0 is assigned to snow covered pixels which will 'cancel' HFI
    # values when the rasters are multiplied later on. QA values in the original data are
    # assigned a value of 1 so they dont impact HFI calculations for now.
    classified = np.where((snow_source > 10) & (snow_source <= 100), 0, 1)
    return WPSDataset.from_array(classified, snow_source, datatype=gdal.GDT_Byte)


def apply_snow_mask(hfi_path: str, last_processed_snow: ProcessedSnow, temp_dir: str) -> str:
    with gdal_s3_context():
        bucket = config.get("OBJECT_STORE_BUCKET")
        for_date = last_processed_snow.for_date
        # The filename of the snow coverage tiff in our object store, prepended with "vsis3" - which
        # tells GDAL to use it's S3 virtual file system driver to read the file.
        # https://gdal.org/user/virtual_file_systems.html
        snow_key = f"/vsis3/{bucket}/snow_coverage/{for_date.strftime('%Y-%m-%d')}/clipped_snow_coverage_{for_date.strftime('%Y-%m-%d')}_epsg4326.tif"
        masked_hfi_path = os.path.join(temp_dir, MASKED_HFI_PATH_NAME)

        with (
            WPSDataset(hfi_path, output_path=masked_hfi_path) as hfi_source,
            WPSDataset(snow_key) as snow_source,
        ):
            # Reproject the snow coverage data to match the HFI grid (same projection, extent and
            # pixel size), classify it into a mask, then apply that mask to the HFI raster.
            with (
                snow_source.warp_to_match(hfi_source) as warped_snow,
                classify_snow_mask(warped_snow) as snow_mask,
            ):
                # The snow mask has values of 0 (snow covered) or 1 (snow free); multiplying
                # applies the mask.
                masked = hfi_source * snow_mask
                masked.ds.GetRasterBand(1).SetNoDataValue(0)
                masked.ds.FlushCache()

    return masked_hfi_path
