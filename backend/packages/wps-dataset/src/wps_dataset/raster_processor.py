"""
Generic windowed multi-raster processing engine using GDAL and numpy.

`iter_tiles` reads matching windows from any number of already-aligned raster bands together,
one tile at a time, so callers can combine several rasters (e.g. classify one, mask it with
another) without holding any of them in memory as a whole. `warp_to_match_vrt` aligns a raster
to another's grid lazily via a warped VRT, so even a reprojection needed to align two rasters
doesn't force materializing the whole warped raster before tiling starts - only the pixels
covering each requested window get warped, on read.
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Callable, Iterator, Sequence

import numpy as np
from osgeo import gdal

logger = logging.getLogger(__name__)

# Raise Python exceptions instead of printing to stderr
gdal.UseExceptions()


@dataclass
class TileConfig:
    tile_width: int = 512
    tile_height: int = 512


def iter_tiles(
    bands: Sequence[gdal.Band],
    x_size: int,
    y_size: int,
    config: TileConfig | None = None,
) -> Iterator[tuple[int, int, int, int, list[np.ndarray]]]:
    """
    Yield (col_off, row_off, width, height, tiles) windows across `bands` together - `tiles`
    has one array per band, all read from the same window, so multiple aligned rasters can be
    processed tile by tile without any of them being read into memory as a whole.
    """
    config = config or TileConfig()
    for row_off in range(0, y_size, config.tile_height):
        h = min(config.tile_height, y_size - row_off)
        for col_off in range(0, x_size, config.tile_width):
            w = min(config.tile_width, x_size - col_off)
            tiles = [band.ReadAsArray(col_off, row_off, w, h) for band in bands]
            yield col_off, row_off, w, h, tiles


def create_output_dataset(
    path: str | None,
    src_ds: gdal.Dataset,
    dtype=gdal.GDT_Byte,
    band_count: int = 1,
) -> gdal.Dataset:
    """
    Create an output raster matching the source's extent and projection: a tiled, compressed
    GeoTIFF at `path`, or an in-memory MEM dataset when `path` is None.
    """
    if path is None:
        driver = gdal.GetDriverByName("MEM")
        dst_ds = driver.Create("", src_ds.RasterXSize, src_ds.RasterYSize, band_count, dtype)
    else:
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


def warp_to_match_vrt(
    src_ds: gdal.Dataset,
    match_ds: gdal.Dataset,
    resample_alg: int = gdal.GRA_NearestNeighbour,
) -> gdal.Dataset:
    """
    Return a warped VRT of `src_ds`, reprojected and resampled to match `match_ds`'s grid
    (projection, extent, and pixel size) - lazily. Unlike a normal gdal.Warp() to a GeoTIFF
    (which fully materializes the output raster before returning), a VRT destination only
    records the warp transform; reading a window from the returned dataset's band warps just
    the source pixels covering that window, on demand. That makes it safe to pass straight to
    `iter_tiles` alongside a raster already on the target grid - the warped source is still
    never read into memory as a whole.
    """
    geotransform = match_ds.GetGeoTransform()
    x_res = geotransform[1]
    y_res = -geotransform[5]
    minx = geotransform[0]
    maxy = geotransform[3]
    maxx = minx + geotransform[1] * match_ds.RasterXSize
    miny = maxy + geotransform[5] * match_ds.RasterYSize

    # ponytail: the /vsimem/ VRT descriptor (a small XML blob, not pixel data) is never
    # gdal.Unlink'd here - fine for short-lived batch processes; add cleanup if this ever runs
    # in a long-lived process where /vsimem/ accumulation would matter.
    vrt_path = f"/vsimem/warp_{uuid.uuid4().hex}.vrt"
    return gdal.Warp(
        vrt_path,
        src_ds,
        format="VRT",
        dstSRS=match_ds.GetProjection(),
        outputBounds=[minx, miny, maxx, maxy],
        xRes=x_res,
        yRes=y_res,
        resampleAlg=resample_alg,
    )


@dataclass
class RasterStep:
    """
    One raster in a processing chain.

    `process(tile, accumulated)` is called with this step's own tile and the result carried
    forward from the previous step (`None` for the chain's first step - there's nothing to
    combine with yet, so it should just return that raster's own prepared tile). Whatever it
    returns becomes `accumulated` for the next step, and is the output tile if this is the
    last step.

    `align` (default True) has this step's dataset warped onto the first step's grid lazily,
    via `warp_to_match_vrt`, if it isn't already on it. Set it False to instead require this
    step's dataset to already exactly match the first step's grid (dimensions, projection, and
    origin) - `process_raster_chain` raises ValueError up front if it doesn't, rather than
    silently reprojecting something that was expected to already line up.
    """

    ds: gdal.Dataset
    process: Callable[[np.ndarray, np.ndarray | None], np.ndarray]
    resample_alg: int = gdal.GRA_NearestNeighbour
    align: bool = True
    band_index: int = 1


def _validate_matches_grid(ds: gdal.Dataset, reference_ds: gdal.Dataset) -> None:
    """Raise ValueError if `ds` isn't already on the same grid as `reference_ds`."""
    if ds.RasterXSize != reference_ds.RasterXSize or ds.RasterYSize != reference_ds.RasterYSize:
        raise ValueError("The dimensions of the two rasters do not match.")
    if ds.GetProjection() != reference_ds.GetProjection():
        raise ValueError("The projections of the two rasters do not match.")
    reference_gt = reference_ds.GetGeoTransform()
    gt = ds.GetGeoTransform()
    if gt[0] != reference_gt[0] or gt[3] != reference_gt[3]:
        raise ValueError("The origins of the two rasters do not match.")


def process_raster_chain(
    output_path: str | None,
    steps: Sequence[RasterStep],
    tile_config: TileConfig | None = None,
    output_dtype=gdal.GDT_Byte,
    output_nodata: float | None = None,
) -> gdal.Dataset:
    """
    Run a chain of two or more raster processing steps tile by tile and write the combined
    result to `output_path` (or an in-memory MEM dataset when `output_path` is None). The
    first step's dataset defines the output grid; every other `align`-ing step's dataset is
    aligned to it lazily via `warp_to_match_vrt`, so no raster in the chain - including any
    that need reprojecting - is ever read into memory as a whole.

    For each tile, `steps[0].process(tile, None)` runs first, then each subsequent step's
    `process(tile, accumulated)` folds its own tile into the running result - e.g. classify the
    first raster, then mask it against the second, then a third, and so on.

    Returns the resulting dataset, still open - the caller owns it and is responsible for
    closing it (e.g. `result = None`) once done, same as any other GDAL write handle.
    """
    if len(steps) < 2:
        raise ValueError("process_raster_chain requires at least 2 steps")

    tile_config = tile_config or TileConfig()
    reference_ds = steps[0].ds
    x_size = reference_ds.RasterXSize
    y_size = reference_ds.RasterYSize

    # Validate every non-aligning step's grid up front, before creating the output dataset or
    # reading any pixels - so a mismatch is reported before any work happens, not partway in.
    for step in steps[1:]:
        if not step.align:
            _validate_matches_grid(step.ds, reference_ds)

    # Keep every warped dataset alive for the life of this function - a gdal.Band doesn't hold
    # a reference back to its parent gdal.Dataset, so letting one get garbage collected (e.g.
    # by only keeping the last loop iteration's `aligned_ds` around) would invalidate any band
    # already pulled from it.
    aligned_datasets: list[gdal.Dataset] = []
    bands = [reference_ds.GetRasterBand(steps[0].band_index)]
    for step in steps[1:]:
        if step.align:
            aligned_ds = warp_to_match_vrt(step.ds, reference_ds, step.resample_alg)
            aligned_datasets.append(aligned_ds)
            bands.append(aligned_ds.GetRasterBand(step.band_index))
        else:
            bands.append(step.ds.GetRasterBand(step.band_index))

    out_ds = create_output_dataset(output_path, reference_ds, dtype=output_dtype)
    out_band = out_ds.GetRasterBand(1)
    if output_nodata is not None:
        out_band.SetNoDataValue(output_nodata)

    for col_off, row_off, w, h, tiles in iter_tiles(bands, x_size, y_size, tile_config):
        accumulated = None
        for step, tile in zip(steps, tiles):
            accumulated = step.process(tile, accumulated)
        out_band.WriteArray(accumulated, col_off, row_off)

    out_band.FlushCache()
    out_ds.FlushCache()
    return out_ds
