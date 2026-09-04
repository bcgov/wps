"""
Windowed raster classification using GDAL, numpy and pandas.
When dealing with large rasters too big to read into memory all at once,
`classify_raster` reads one tile at a time, classifies it, and writes to an output raster.
It also accumulates per-class pixel counts and returns a summary DataFrame.
"""

import logging
import time
from dataclasses import dataclass

import numpy as np
import pandas
from osgeo import gdal

logger = logging.getLogger(__name__)


# Raise Python exceptions instead of printing to stderr
gdal.UseExceptions()

# uint8 sentinel for nodata output pixels, distinct from any real ClassRule.label
NODATA_LABEL = 255


@dataclass
class ClassRule:
    label: int
    name: str
    min_val: float  # inclusive
    max_val: float  # exclusive (except last class)


def hfi_classify_rules() -> list[ClassRule]:
    return [
        ClassRule(0, "below_4000", float("-inf"), 4000),
        ClassRule(1, "above_4000", 4000, 10000),
        ClassRule(2, "above_10000", 10000, float("inf")),
    ]


def snow_classify_rules() -> list[ClassRule]:
    return [
        ClassRule(0, "snow_covered", 10, 100),
        ClassRule(1, "snow_free", float("-inf"), 10),
    ]


@dataclass
class TileConfig:
    tile_width: int = 512
    tile_height: int = 512


def classify_raster(
    input_path: str,
    output_path: str,
    rules: list[ClassRule],
    band_index: int = 1,
    config: TileConfig | None = None,
) -> pandas.DataFrame:
    """Single-band windowed classification.

    Reads one tile at a time from `band_index`, classifies it,
    writes to output, and accumulates per-class pixel counts.
    Returns a Pandas summary DataFrame.
    """
    config = config or TileConfig()
    src_ds = gdal.Open(input_path, gdal.GA_ReadOnly)
    if src_ds is None:
        raise FileNotFoundError(f"Cannot open {input_path}")

    raster_w = src_ds.RasterXSize
    raster_h = src_ds.RasterYSize
    src_band = src_ds.GetRasterBand(band_index)
    nodata = src_band.GetNoDataValue()

    logger.info(f"Input: {raster_w}×{raster_h}, nodata={nodata}")

    dst_ds = _create_output_dataset(output_path, src_ds)
    dst_band = dst_ds.GetRasterBand(1)
    dst_band.SetNoDataValue(NODATA_LABEL)

    # Per-class accumulators, keyed by output pixel value
    counts: dict[int, int] = {}

    t0 = time.perf_counter()
    tiles_done = 0
    total_tiles = ((raster_w + config.tile_width - 1) // config.tile_width) * (
        (raster_h + config.tile_height - 1) // config.tile_height
    )

    for row_off in range(0, raster_h, config.tile_height):
        for col_off in range(0, raster_w, config.tile_width):
            w = min(config.tile_width, raster_w - col_off)
            h = min(config.tile_height, raster_h - row_off)

            # ---- READ ----
            tile = src_band.ReadAsArray(col_off, row_off, w, h).astype(np.float64)

            # ---- CLASSIFY ----
            classified = classify_array(tile, rules, nodata)

            # ---- WRITE ----
            dst_band.WriteArray(classified, col_off, row_off)

            # ---- ACCUMULATE ----
            labels, cnts = np.unique(classified, return_counts=True)
            for lbl, cnt in zip(labels, cnts):
                counts[int(lbl)] = counts.get(int(lbl), 0) + int(cnt)

            tiles_done += 1
            if tiles_done % 50 == 0 or tiles_done == total_tiles:
                elapsed = time.perf_counter() - t0
                logger.debug(f"  tiles: {tiles_done}/{total_tiles}  ({elapsed:.1f}s)")

    # Flush and close
    dst_band.FlushCache()
    dst_ds.FlushCache()
    dst_ds = None
    src_ds = None

    logger.info(f"Wrote {output_path}")
    return _build_summary(rules, counts)


def classify_array(
    data: np.ndarray,
    rules: list[ClassRule],
    nodata: float | None = None,
) -> np.ndarray:
    """Classify a 2-D array of pixel values into class labels (uint8)."""
    assert all(rule.label != NODATA_LABEL for rule in rules), (
        f"ClassRule.label must not use the nodata sentinel {NODATA_LABEL}"
    )
    out = np.zeros(data.shape, dtype=np.uint8)

    # Mask nodata first
    if nodata is not None:
        invalid = np.isnan(data) | (data == nodata)
    else:
        invalid = np.isnan(data)
    valid = ~invalid

    for rule in rules:
        mask = valid & (data >= rule.min_val) & (data < rule.max_val)
        out[mask] = rule.label

    out[invalid] = NODATA_LABEL
    return out


def _create_output_dataset(
    path: str,
    src_ds: gdal.Dataset,
    dtype=gdal.GDT_Byte,
    band_count: int = 1,
) -> gdal.Dataset:
    """Create an output GeoTIFF matching the source's extent and projection."""
    driver = gdal.GetDriverByName("GTiff")
    dst_ds = driver.Create(
        path,
        src_ds.RasterXSize,
        src_ds.RasterYSize,
        band_count,
        dtype,
        options=["TILED=YES", "COMPRESS=LZW", "BIGTIFF=YES"],
    )
    dst_ds.SetGeoTransform(src_ds.GetGeoTransform())
    dst_ds.SetProjection(src_ds.GetProjection())
    return dst_ds


def _build_summary(rules: list[ClassRule], counts: dict[int, int]) -> pandas.DataFrame:
    total = sum(counts.values())

    def pct(count: int) -> float:
        return round(count / total * 100, 2) if total else 0.0

    nodata_count = counts.get(NODATA_LABEL, 0)
    rows = [
        {
            "label": NODATA_LABEL,
            "class_name": "nodata",
            "pixel_count": nodata_count,
            "pct": pct(nodata_count),
        }
    ]
    for rule in rules:
        rule_count = counts.get(rule.label, 0)
        rows.append(
            {
                "label": rule.label,
                "class_name": rule.name,
                "pixel_count": rule_count,
                "pct": pct(rule_count),
            }
        )
    return pandas.DataFrame(rows)
