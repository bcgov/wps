"""
Windowed HFI classification + snow masking, built on the generic raster_processor engine.

Classifies the raw HFI raster and applies the snow-coverage mask in a single tiled pass -
neither the HFI raster nor the (reprojected) snow raster is ever fully materialized in memory,
or written to disk in an intermediate form. This is an alternative to the existing
classify_hfi() + apply_snow_mask() two-step (classify_hfi.py / snow.py), kept in its own file
for isolated review before deciding whether to wire it into process_hfi.py in that pair's place.
"""

import logging
import os

import numpy as np
from osgeo import gdal
from wps_dataset.raster_processor import RasterStep, TileConfig, process_raster_chain
from wps_shared import config
from wps_shared.db.models.snow import ProcessedSnow
from wps_shared.utils.s3 import gdal_s3_context

from app.auto_spatial_advisory.snow import MASKED_HFI_PATH_NAME

logger = logging.getLogger(__name__)


def _classify_hfi_tile(data: np.ndarray, nodata: float | None) -> np.ndarray:
    """
    Mirrors classify_hfi.py's bucketing: 0 = below 4000 (or nodata), 1 = 4000-10000, 2 = above
    10000. Nodata and "below 4000" intentionally share output value 0, since downstream
    polygonization (process_hfi.py) treats 0 as nodata and excludes those pixels entirely -
    only advisory (1) and warning (2) areas are ever polygonized.
    """
    invalid = np.isnan(data) if nodata is None else np.isnan(data) | (data == nodata)
    classified = np.select(
        [invalid, data < 4000, data < 10000],
        [0, 0, 1],
        default=2,
    )
    return classified.astype(np.uint8)


def _snow_mask_tile(data: np.ndarray) -> np.ndarray:
    """Mirrors snow.py's classify_snow_mask: 0 where snow-covered (10 < NDSI <= 100), 1 elsewhere."""
    return np.where((data > 10) & (data <= 100), 0, 1).astype(np.uint8)


def generate_snow_masked_hfi(
    hfi_path: str,
    last_processed_snow: ProcessedSnow,
    temp_dir: str,
    tile_config: TileConfig | None = None,
) -> str:
    """
    Classify the raw HFI raster and apply the snow-coverage mask in a single windowed pass, as
    a 2-step raster chain: classify the HFI tile, then mask it against the (lazily
    grid-aligned) snow tile. Neither raster is ever held in memory as a whole, and no
    intermediate classified.tif is written and re-read as classify_hfi() + apply_snow_mask()
    currently do.

    :param hfi_path: path to the raw (unclassified) HFI GeoTIFF
    """
    with gdal_s3_context():
        bucket = config.get("OBJECT_STORE_BUCKET")
        for_date = last_processed_snow.for_date
        snow_key = (
            f"/vsis3/{bucket}/snow_coverage/{for_date.strftime('%Y-%m-%d')}/"
            f"clipped_snow_coverage_{for_date.strftime('%Y-%m-%d')}_epsg4326.tif"
        )
        masked_hfi_path = os.path.join(temp_dir, MASKED_HFI_PATH_NAME)

        hfi_ds = gdal.Open(hfi_path, gdal.GA_ReadOnly)
        snow_ds = gdal.Open(snow_key, gdal.GA_ReadOnly)
        hfi_nodata = hfi_ds.GetRasterBand(1).GetNoDataValue()

        def classify_step(tile: np.ndarray, _accumulated: np.ndarray | None) -> np.ndarray:
            return _classify_hfi_tile(tile.astype(np.float64), hfi_nodata)

        def mask_step(tile: np.ndarray, accumulated: np.ndarray | None) -> np.ndarray:
            return accumulated * _snow_mask_tile(tile)

        # process_raster_chain returns the output still open; its return value is discarded
        # here rather than captured, which closes it immediately (the writer's directory
        # structure isn't finalized until closed, and callers reopen masked_hfi_path right away).
        process_raster_chain(
            masked_hfi_path,
            [RasterStep(hfi_ds, classify_step), RasterStep(snow_ds, mask_step)],
            tile_config=tile_config,
            output_nodata=0,
        )
        snow_ds = None
        hfi_ds = None

    return masked_hfi_path
