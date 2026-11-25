"""Build continuous COGs without blending Non-fuel/water into adjacent fuel."""

import logging

import numpy as np
from numpy.typing import NDArray
from osgeo import gdal
from wps_shared.geospatial.cog import warp_to_memory, write_cog
from wps_shared.geospatial.geospatial import GDALResamplingMethod, SpatialReferenceSystem
from wps_shared.geospatial.wps_dataset import WPSDataset

logger = logging.getLogger(__name__)


def generate_fuel_aware_cog(
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
        values = dataset.read_array()
        datatype = source.GetRasterBand(1).DataType
        # GDAL must compare against the stored pixel value, not an unrepresentable Float64 marker.
        nodata = values.dtype.type(nodata).item()

        # Pixels outside the source footprint (e.g. outside BC) stay NoData even where the fuel
        # grid says Non-fuel, so only Non-fuel pixels that have a source value are kept.
        valid_non_fuel_mask = non_fuel_mask & np.isfinite(values) & (values != nodata)
        with (
            WPSDataset.from_array(
                np.where(non_fuel_mask, nodata, values), dataset, nodata, datatype=datatype
            ) as fuel_only,
            WPSDataset.from_array(
                np.where(valid_non_fuel_mask, values, nodata), dataset, nodata, datatype=datatype
            ) as non_fuel_only,
        ):
            # Interpolate only fuel pixels. Both warps use the same source grid.
            warped_fuel = warp_to_memory(fuel_only.as_gdal_ds(), target_srs, resample_alg)
            warped_non_fuel = warp_to_memory(
                non_fuel_only.as_gdal_ds(), target_srs, GDALResamplingMethod.NEAREST_NEIGHBOUR
            )

            # Put the Non-fuel/water values back over the interpolated result.
            warped_band = warped_fuel.GetRasterBand(1)
            warped_values = warped_band.ReadAsArray()
            non_fuel_values = warped_non_fuel.GetRasterBand(1).ReadAsArray()
            restore_non_fuel_mask = non_fuel_values != nodata
            warped_values[restore_non_fuel_mask] = non_fuel_values[restore_non_fuel_mask]
            warped_band.WriteArray(warped_values)

            # Nearest-neighbour overviews avoid averaging restored values with fuel or NoData.
            write_cog(
                warped_fuel,
                output_path,
                overview_resample_alg=GDALResamplingMethod.NEAREST_NEIGHBOUR,
            )

    logger.info("COG created at %s", output_path)
    return output_path
