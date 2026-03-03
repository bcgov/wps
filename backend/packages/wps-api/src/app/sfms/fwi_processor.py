import logging
from time import perf_counter
from typing import Optional

import numpy as np

from wps_shared.fwi import vectorized_bui, vectorized_dc, vectorized_dmc, vectorized_ffmc, vectorized_fwi, vectorized_isi
from wps_shared.geospatial.wps_dataset import WPSDataset

logger = logging.getLogger(__name__)


def check_weather_values(rh_array: Optional[np.ndarray] = None, precip_array: Optional[np.ndarray] = None, ws_array: Optional[np.ndarray] = None) -> None:
    """
    Logs errors if any weather condition values are out of acceptable ranges.

    :param rh_array: Optional array of relative humidity values (0–100).
    :param prec_array: Optional array of precipitation values (>= 0).
    :param ws_array: Optional array of wind speed values (>= 0).
    """
    if rh_array is not None and ((rh_array < 0).any() or (rh_array > 100).any()):
        min_rh = rh_array.min()
        max_rh = rh_array.max()
        logger.error(f"Relative humidity values out of bounds (min: {min_rh}, max: {max_rh})")

    if precip_array is not None and (precip_array < 0).any():
        min_precip = precip_array.min()
        logger.error(f"Precipitation contains negative values (min: {min_precip})")

    if ws_array is not None and (ws_array < 0).any():
        min_ws = ws_array.min()
        logger.error(f"Wind speed contains negative values (min: {min_ws})")


def calculate_dc(dc_ds: WPSDataset, temp_ds: WPSDataset, rh_ds: WPSDataset, precip_ds: WPSDataset, latitude: np.ndarray, month: np.ndarray):
    dc_array, _ = dc_ds.replace_nodata_with(0)
    temp_array, _ = temp_ds.replace_nodata_with(0)
    rh_array, _ = rh_ds.replace_nodata_with(0)
    precip_array, _ = precip_ds.replace_nodata_with(0)

    check_weather_values(rh_array, precip_array)

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

    check_weather_values(rh_array, precip_array)

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


def calculate_ffmc(previous_ffmc_ds: WPSDataset, temp_ds: WPSDataset, rh_ds: WPSDataset, precip_ds: WPSDataset, wind_speed_ds: WPSDataset):
    previous_ffmc_array, _ = previous_ffmc_ds.replace_nodata_with(0)
    temp_array, _ = temp_ds.replace_nodata_with(0)
    rh_array, _ = rh_ds.replace_nodata_with(0)
    precip_array, _ = precip_ds.replace_nodata_with(0)
    wind_speed_array, _ = wind_speed_ds.replace_nodata_with(0)

    check_weather_values(rh_array, precip_array, wind_speed_array)

    start = perf_counter()
    ffmc_values = vectorized_ffmc(previous_ffmc_array, temp_array, rh_array, wind_speed_array, precip_array)
    logger.info("%f seconds to calculate vectorized ffmc", perf_counter() - start)

    nodata_mask, nodata_value = previous_ffmc_ds.get_nodata_mask()
    if nodata_mask is not None:
        ffmc_values[nodata_mask] = nodata_value

    return ffmc_values, nodata_value


def calculate_fwi(isi_ds: WPSDataset, bui_ds: WPSDataset):
    isi_array, _ = isi_ds.replace_nodata_with(0)
    bui_array, _ = bui_ds.replace_nodata_with(0)

    start = perf_counter()
    fwi_values = vectorized_fwi(isi_array, bui_array)
    logger.info("%f seconds to calculate vectorized fwi", perf_counter() - start)

    nodata_mask, nodata_value = isi_ds.get_nodata_mask()
    if nodata_mask is not None:
        fwi_values[nodata_mask] = nodata_value

    return fwi_values, nodata_value


def calculate_isi(ffmc_ds: WPSDataset, wind_speed_ds: WPSDataset):
    ffmc_array, _ = ffmc_ds.replace_nodata_with(0)
    wind_speed_array, _ = wind_speed_ds.replace_nodata_with(0)

    start = perf_counter()
    isi_values = vectorized_isi(ffmc_array, wind_speed_array, False)
    logger.info("%f seconds to calculate vectorized ffmc", perf_counter() - start)

    nodata_mask, nodata_value = ffmc_ds.get_nodata_mask()
    if nodata_mask is not None:
        isi_values[nodata_mask] = nodata_value

    return isi_values, nodata_value
