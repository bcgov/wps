"""Memory-bounded helpers for statistics over rasters on the same grid."""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

import numpy as np
from osgeo import gdal

from wps_shared.geospatial.geospatial import rasters_match

DEFAULT_WINDOW_SIZE = 256
ZoneValueKey = tuple[int, int]
ZoneValueCounts = dict[ZoneValueKey, int]


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
) -> ZoneValueCounts:
    """Count selected categorical raster values grouped by zone.

    Only pixels selected by `included_pixels` are counted. Returned keys are ordered as
    `(zone_id, categorical_value)`.

    Zone/category pairs are encoded as one dimensional integer keys so `np.bincount` can count
    them without constructing and sorting a two column array. Included zone IDs and values must
    be non-negative integers, and memory use grows with the largest encoded pair.

    """
    if not np.any(included_pixels):
        return {}

    # convert before multiplication so encoding is independent of the raster's integer width
    selected_zone_ids = zone_ids[included_pixels].astype(np.int64)
    selected_values = values[included_pixels].astype(np.int64)

    # reserve one range of keys per zone so each (zone, category) pair maps to one integer;
    # with a category range size of 4, (zone 10, category 2) becomes 10 * 4 + 2 = 42,
    # and divmod(42, 4) recovers (10, 2)
    category_range_size = int(selected_values.max()) + 1
    encoded_pairs = selected_zone_ids * category_range_size + selected_values
    frequencies = np.bincount(encoded_pairs)

    counts: ZoneValueCounts = {}
    for encoded_pair in np.flatnonzero(frequencies):
        zone_id, category = divmod(int(encoded_pair), category_range_size)
        counts[(zone_id, category)] = int(frequencies[encoded_pair])
    return counts


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
