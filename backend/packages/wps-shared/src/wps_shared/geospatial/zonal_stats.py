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
    """Count categorical values by fire zone source identifier.

    The boolean `included_pixels` mask owns domain rules such as HFI thresholds and nodata.
    Each returned key is ordered as `(source_identifier, categorical_value)`. Source identifiers
    are raster values, not advisory-shape database IDs.

    For example, a result may look like ``{(101, 3): 12, (101, 4): 5, (202, 3): 8}``.
    """
    if not np.any(included_pixels):
        return {}

    unique_pairs, frequencies = np.unique(
        np.column_stack((zone_ids[included_pixels], values[included_pixels])),
        axis=0,
        return_counts=True,
    )
    counts: ZoneValueCounts = {
        (int(source_identifier), int(value)): int(frequency)
        for (source_identifier, value), frequency in zip(
            unique_pairs.tolist(), frequencies.tolist()
        )
    }
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
