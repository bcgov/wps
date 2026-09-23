"""Memory-bounded helpers for statistics over rasters on the same grid."""

from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np

from wps_shared.geospatial.geospatial import rasters_match
from wps_shared.geospatial.wps_dataset import WPSDataset

ZoneValueKey = tuple[int, int]
ZoneValueCounts = dict[ZoneValueKey, int]


@dataclass(frozen=True)
class AlignedRasterWindow:
    """Ordered raster arrays and their shared pixel offsets for one window."""

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
    them without constructing and sorting a two column array. This significantly reduces counting
    time across the many windows in higher resolution rasters such as the 50 m TPI. Included zone
    IDs and values must be non negative integers, and memory use grows with the largest encoded
    pair.
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


def iter_aligned_raster_windows(
    reference: WPSDataset,
    aligned_dataset: WPSDataset,
    *additional_datasets: WPSDataset,
    window_size: int | None = None,
) -> Iterator[AlignedRasterWindow]:
    """Yield arrays from two or more aligned rasters without loading them entirely.

    The reference dataset defines the window grid. Every other dataset must match that grid
    exactly. Arrays are returned in the same order as the dataset arguments.
    """
    aligned_datasets = (aligned_dataset, *additional_datasets)
    for dataset in aligned_datasets:
        if not rasters_match(reference.ds, dataset.ds):
            raise ValueError(f"Raster grid does not match reference: {dataset.ds.GetDescription()}")

    for window in reference.iter_windows(window_size):
        yield AlignedRasterWindow(
            x_offset=window.x_offset,
            y_offset=window.y_offset,
            width=window.width,
            height=window.height,
            arrays=(window.array,)
            + tuple(dataset.read_window(window) for dataset in aligned_datasets),
        )
