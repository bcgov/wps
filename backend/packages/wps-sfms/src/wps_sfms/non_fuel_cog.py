"""Build continuous COGs without blending Non-fuel/water into adjacent fuel."""

import logging

import numpy as np
from numpy.typing import NDArray
from osgeo import gdal
from wps_shared.geospatial.cog import warp_to_memory, write_cog
from wps_shared.geospatial.geospatial import GDALResamplingMethod, SpatialReferenceSystem
from wps_shared.geospatial.wps_dataset import WPSDataset

logger = logging.getLogger(__name__)


def _copy_with_values(source: gdal.Dataset, values: np.ndarray, nodata: float) -> gdal.Dataset:
    """In-memory copy of ``source`` (keeps georeferencing, NoData and band metadata) with new values."""
    copy = gdal.Translate("", source, format="MEM")
    band = copy.GetRasterBand(1)
    band.SetNoDataValue(nodata)
    band.WriteArray(values)
    return copy


def generate_non_fuel_cog(
    dataset: WPSDataset,
    output_path: str,
    non_fuel_mask: NDArray[np.bool_],
    resample_alg: GDALResamplingMethod = GDALResamplingMethod.BILINEAR,
) -> str:
    """Write a COG where Non-fuel/water pixels don't affect the interpolation of fuel pixels.

    GDAL resampling ignores NoData, so Non-fuel/water pixels are set to NoData while warping.
    Their original values are then put back using nearest neighbour, so they stay valid
    (e.g. 0 for fire behaviour outputs) instead of showing as gaps or blended values.
    The source dataset is not modified.
    """
    source = dataset.as_gdal_ds()
    if source.RasterCount != 1:
        raise ValueError("Non-fuel COG generation requires a single-band source")
    if non_fuel_mask.dtype != np.bool_:
        raise ValueError("Non-fuel mask must contain boolean values")
    if non_fuel_mask.shape != (source.RasterYSize, source.RasterXSize):
        raise ValueError("Non-fuel mask does not match the source raster shape")
    nodata = dataset.require_nodata_value()

    logger.info("Generating Non-fuel-aware COG: %s", output_path)
    target_srs = SpatialReferenceSystem.WEB_MERCATOR.srs
    with gdal.ExceptionMgr():
        values = source.GetRasterBand(1).ReadAsArray()
        # GDAL must compare against the stored pixel value, not an unrepresentable Float64 marker.
        nodata = values.dtype.type(nodata).item()

        # Warp with Non-fuel/water as NoData so only fuel pixels are interpolated.
        fuel_only = _copy_with_values(source, np.where(non_fuel_mask, nodata, values), nodata)
        warped = warp_to_memory(fuel_only, target_srs, resample_alg)

        # Warp only the Non-fuel/water values with nearest neighbour. Both copies share the
        # source's georeferencing, so GDAL produces the same output grid for both warps.
        # Pixels outside the source footprint (e.g. outside BC) stay NoData even where the fuel
        # grid says Non-fuel, so only Non-fuel pixels that have a source value are kept.
        keep = non_fuel_mask & np.isfinite(values) & (values != nodata)
        non_fuel_only = _copy_with_values(source, np.where(keep, values, nodata), nodata)
        warped_non_fuel = warp_to_memory(
            non_fuel_only, target_srs, GDALResamplingMethod.NEAREST_NEIGHBOUR
        )

        # Put the Non-fuel/water values back over the interpolated result.
        warped_band = warped.GetRasterBand(1)
        warped_values = warped_band.ReadAsArray()
        non_fuel_values = warped_non_fuel.GetRasterBand(1).ReadAsArray()
        restored = non_fuel_values != nodata
        warped_values[restored] = non_fuel_values[restored]
        warped_band.WriteArray(warped_values)

        # Nearest used in overviews so restored values aren't averaged with fuel (or NoData) at low zoom.
        write_cog(warped, output_path, overview_resample_alg=GDALResamplingMethod.NEAREST_NEIGHBOUR)

    logger.info("COG created at %s", output_path)
    return output_path
