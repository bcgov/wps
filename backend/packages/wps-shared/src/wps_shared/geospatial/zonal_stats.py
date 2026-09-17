"""Memory-bounded helpers for statistics over rasters on the same grid."""

import math
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

import numpy as np
from osgeo import gdal

from wps_shared.geospatial.geospatial import rasters_match

DEFAULT_WINDOW_SIZE = 256


@dataclass(frozen=True)
class RasterWindow:
    """Arrays and their shared pixel offsets for one bounded raster window."""

    x_offset: int
    y_offset: int
    width: int
    height: int
    arrays: tuple[np.ndarray, ...]


def count_values_by_zone(
    zone_ids: np.ndarray, values: np.ndarray, included_pixels: np.ndarray
) -> dict[tuple[int, int], int]:
    """Count caller-selected categorical values by fire-zone source identifier.

    The boolean ``included_pixels`` mask owns domain rules such as HFI thresholds and nodata.
    Returned keys contain raster source identifiers, not advisory-shape database IDs.
    """
    if not np.any(included_pixels):
        return {}

    unique_pairs, frequencies = np.unique(
        np.column_stack((zone_ids[included_pixels], values[included_pixels])),
        axis=0,
        return_counts=True,
    )
    return {
        (source_identifier, value): frequency
        for (source_identifier, value), frequency in zip(
            unique_pairs.tolist(), frequencies.tolist()
        )
    }


def iter_raster_windows(
    datasets: Sequence[gdal.Dataset], window_size: int = DEFAULT_WINDOW_SIZE
) -> Iterator[RasterWindow]:
    """Yield aligned single-band arrays without loading complete rasters into memory.

    The first dataset defines the window grid. Every remaining dataset must match that grid
    exactly so arrays at the same offsets describe the same geographic pixels.
    """
    if not datasets:
        return

    reference = datasets[0]
    for dataset in datasets[1:]:
        if not rasters_match(reference, dataset):
            raise ValueError(f"Raster grid does not match reference: {dataset.GetDescription()}")
    bands = [dataset.GetRasterBand(1) for dataset in datasets]
    for y_offset in range(0, reference.RasterYSize, window_size):
        height = min(window_size, reference.RasterYSize - y_offset)
        for x_offset in range(0, reference.RasterXSize, window_size):
            width = min(window_size, reference.RasterXSize - x_offset)
            yield RasterWindow(
                x_offset=x_offset,
                y_offset=y_offset,
                width=width,
                height=height,
                arrays=tuple(band.ReadAsArray(x_offset, y_offset, width, height) for band in bands),
            )


def pixel_area(dataset: gdal.Dataset) -> float:
    """Return one north-up pixel's area in the squared units of the raster projection."""
    geotransform = dataset.GetGeoTransform()
    return abs(geotransform[1] * geotransform[5])


def sample_band_at_coordinate(
    dataset: gdal.Dataset, x_coordinate: float, y_coordinate: float
) -> int | float | None:
    """Read one pixel at a coordinate in the dataset projection, or None when outside it."""
    inverse = gdal.InvGeoTransform(dataset.GetGeoTransform())
    pixel_x, pixel_y = gdal.ApplyGeoTransform(inverse, x_coordinate, y_coordinate)
    column = math.floor(pixel_x)
    row = math.floor(pixel_y)
    if column < 0 or row < 0 or column >= dataset.RasterXSize or row >= dataset.RasterYSize:
        return None

    value = dataset.GetRasterBand(1).ReadAsArray(column, row, 1, 1)[0, 0]
    return value.item() if isinstance(value, np.generic) else value
