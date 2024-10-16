from time import perf_counter
import logging
import numpy as np
from osgeo import gdal

from app.sfms.bui import replace_nodata_with_zero
from app.auto_spatial_advisory.sfms import vectorized_dmc, vectorized_dc

logger = logging.getLogger(__name__)


def calculate_dc(dc_ds: gdal.Dataset, temp_ds: gdal.Dataset, rh_ds: gdal.Dataset, precip_ds: gdal.Dataset, latitude: np.ndarray, month: np.ndarray):
    dmc_array, dmc_nodata_value = replace_nodata_with_zero(dc_ds)
    temp_array, _ = replace_nodata_with_zero(temp_ds)
    rh_array, _ = replace_nodata_with_zero(rh_ds)
    precip_array, _ = replace_nodata_with_zero(precip_ds)

    start = perf_counter()
    dc_values = vectorized_dc(dmc_array, temp_array, rh_array, precip_array, latitude, month, True)
    logger.info("%f seconds to calculate vectorized dc", perf_counter() - start)

    if dmc_nodata_value is not None:
        nodata_mask = dc_ds.GetRasterBand(1).ReadAsArray() == dmc_nodata_value
        dc_values[nodata_mask] = dmc_nodata_value

    return dc_values, dmc_nodata_value


def calculate_dmc(dmc_ds: gdal.Dataset, temp_ds: gdal.Dataset, rh_ds: gdal.Dataset, precip_ds: gdal.Dataset, latitude: np.ndarray, month: np.ndarray):
    dmc_array, dmc_nodata_value = replace_nodata_with_zero(dmc_ds)
    temp_array, _ = replace_nodata_with_zero(temp_ds)
    rh_array, _ = replace_nodata_with_zero(rh_ds)
    precip_array, _ = replace_nodata_with_zero(precip_ds)

    start = perf_counter()
    dmc_values = vectorized_dmc(dmc_array, temp_array, rh_array, precip_array, latitude, month, True)
    print(perf_counter() - start)

    if dmc_nodata_value is not None:
        nodata_mask = dmc_ds.GetRasterBand(1).ReadAsArray() == dmc_nodata_value
        dmc_values[nodata_mask] = dmc_nodata_value

    return dmc_values, dmc_nodata_value
