from time import perf_counter
import logging
import numpy as np

from app.geospatial.wps_dataset import WPSDataset
from app.auto_spatial_advisory.sfms import vectorized_dmc, vectorized_dc, vectorized_bui

logger = logging.getLogger(__name__)


def calculate_dc(dc_ds: WPSDataset, temp_ds: WPSDataset, rh_ds: WPSDataset, precip_ds: WPSDataset, latitude: np.ndarray, month: np.ndarray):
    dc_array, _ = dc_ds.replace_nodata_with(0)
    temp_array, _ = temp_ds.replace_nodata_with(0)
    rh_array, _ = rh_ds.replace_nodata_with(0)
    precip_array, _ = precip_ds.replace_nodata_with(0)

    start = perf_counter()
    dc_values = vectorized_dc(dc_array, temp_array, rh_array, precip_array, latitude, month, True)
    logger.info("%f seconds to calculate vectorized dc", perf_counter() - start)

    nodata_mask, nodata_value = dc_ds.get_nodata_mask()
    if nodata_mask is not None:
        dc_values[nodata_mask] = nodata_value

    return dc_values, nodata_value


def calculate_dmc(dmc_ds: WPSDataset, temp_ds: WPSDataset, rh_ds: WPSDataset, precip_ds: WPSDataset, latitude: np.ndarray, month: np.ndarray):
    dmc_array, _ = dmc_ds.replace_nodata_with(0)
    temp_array, _ = temp_ds.replace_nodata_with(0)
    rh_array, _ = rh_ds.replace_nodata_with(0)
    precip_array, _ = precip_ds.replace_nodata_with(0)

    start = perf_counter()
    dmc_values = vectorized_dmc(dmc_array, temp_array, rh_array, precip_array, latitude, month, True)
    logger.info("%f seconds to calculate vectorized dmc", perf_counter() - start)

    nodata_mask, nodata_value = dmc_ds.get_nodata_mask()
    if nodata_mask is not None:
        dmc_values[nodata_mask] = nodata_value

    return dmc_values, nodata_value


def calculate_bui(dmc_ds: WPSDataset, dc_ds: WPSDataset):
    dmc_array, _ = dmc_ds.replace_nodata_with(0)
    dc_array, _ = dc_ds.replace_nodata_with(0)

    start = perf_counter()
    bui_values = vectorized_bui(dmc_array, dc_array)
    logger.info("%f seconds to calculate vectorized bui", perf_counter() - start)

    nodata_mask, nodata_value = dmc_ds.get_nodata_mask()
    if nodata_mask is not None:
        bui_values[nodata_mask] = nodata_value

    return bui_values, nodata_value