"""Proof of concept, run classification on HFI GeoTiff"""

import numpy as np
from osgeo import gdal
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.utils.s3 import gdal_s3_context


def classify_hfi(source_path, target_path):
    """
    Given a source path of some HFI GeoTIFF, classify the GeoTIFF and save it to a new GeoTIFF.
    The output GeoTIFF will use 8 bit unsigned values.
    """
    with gdal_s3_context(), WPSDataset(source_path) as source:
        source_data = np.asarray(source)
        classified = np.select([source_data < 4000, source_data < 10000], [0, 1], default=2)
        WPSDataset.from_array(
            classified, source, nodata_value=0, datatype=gdal.GDT_Byte, output_path=target_path
        ).close()
