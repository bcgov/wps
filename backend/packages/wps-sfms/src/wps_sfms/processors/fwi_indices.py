"""Compute functions for FFMC, DMC, DC from raster datasets."""

import logging
from time import perf_counter
from typing import Any, Callable, List, Tuple

import numpy as np

from wps_shared.fwi import vectorized_dc, vectorized_dmc, vectorized_ffmc
from wps_shared.geospatial.wps_dataset import WPSDataset

logger = logging.getLogger(__name__)


def _compute_index(
    index_ds: WPSDataset,
    weather_datasets: List[WPSDataset],
    vectorized_fn: Callable[..., np.ndarray],
    *extra_args: Any,
    label: str = "",
) -> Tuple[np.ndarray, float]:
    """Common boilerplate: nodata replacement, timing, mask reapplication."""
    index_array, _ = index_ds.replace_nodata_with(0)
    weather_arrays = [ds.replace_nodata_with(0)[0] for ds in weather_datasets]

    start = perf_counter()
    values = vectorized_fn(index_array, *weather_arrays, *extra_args)
    logger.info("%f seconds to calculate vectorized %s", perf_counter() - start, label)

    nodata_mask, nodata_value = index_ds.get_nodata_mask()
    if nodata_mask is not None:
        values[nodata_mask] = nodata_value

    return values, nodata_value


def compute_ffmc(
    ffmc_ds: WPSDataset, temp_ds: WPSDataset, rh_ds: WPSDataset, precip_ds: WPSDataset
) -> Tuple[np.ndarray, float]:
    """Calculate FFMC using zero wind speed as placeholder."""
    # Wind speed interpolation not yet available — use zeros as placeholder
    temp_array, _ = temp_ds.replace_nodata_with(0)
    ws_ds = WPSDataset.from_array(
        np.zeros_like(temp_array),
        temp_ds.as_gdal_ds().GetGeoTransform(),
        temp_ds.as_gdal_ds().GetProjection(),
        nodata_value=temp_ds.as_gdal_ds().GetRasterBand(1).GetNoDataValue(),
    )
    return _compute_index(ffmc_ds, [temp_ds, rh_ds, ws_ds, precip_ds], vectorized_ffmc, label="ffmc")


def compute_dmc(
    dmc_ds: WPSDataset, temp_ds: WPSDataset, rh_ds: WPSDataset, precip_ds: WPSDataset,
    month: int,
) -> Tuple[np.ndarray, float]:
    latitude = dmc_ds.generate_latitude_array()
    month_array = np.full(latitude.shape, month)
    return _compute_index(dmc_ds, [temp_ds, rh_ds, precip_ds], vectorized_dmc, latitude, month_array, True, label="dmc")


def compute_dc(
    dc_ds: WPSDataset, temp_ds: WPSDataset, rh_ds: WPSDataset, precip_ds: WPSDataset,
    month: int,
) -> Tuple[np.ndarray, float]:
    latitude = dc_ds.generate_latitude_array()
    month_array = np.full(latitude.shape, month)
    return _compute_index(dc_ds, [temp_ds, rh_ds, precip_ds], vectorized_dc, latitude, month_array, True, label="dc")
