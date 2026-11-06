"""Exclude Non-fuel from continuous COGs; Insights displays classification separately."""

import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from numpy.typing import NDArray
from osgeo import gdal
from wps_shared.geospatial.cog import generate_web_optimized_cog

logger = logging.getLogger(__name__)


def generate_non_fuel_cog(
    input_path: str,
    output_path: str,
    non_fuel_mask: NDArray[np.bool_],
) -> str:
    """Mask classified Non-fuel, not valid zeros, before ordinary COG generation."""
    logger.info("Generating mask-aware fire-behaviour COG: %s -> %s", input_path, output_path)
    with gdal.ExceptionMgr(), gdal.Open(input_path) as source:
        if non_fuel_mask.shape != (source.RasterYSize, source.RasterXSize):
            raise ValueError("Non-fuel mask does not match the source raster shape")
        if non_fuel_mask.dtype != np.bool_:
            raise ValueError("Non-fuel mask must contain boolean values")
        if source.RasterCount != 1:
            raise ValueError("Non-fuel COG generation requires a single-band source")

        # Mask a temporary copy so the original GeoTIFF stays unchanged.
        with TemporaryDirectory() as temp_dir:
            masked_path = str(Path(temp_dir) / "masked.tif")
            with gdal.Translate(masked_path, source, format="GTiff") as masked:
                band = masked.GetRasterBand(1)
                nodata = band.GetNoDataValue()
                if nodata is None:
                    raise ValueError("Non-fuel COG generation requires source NoData")
                values = band.ReadAsArray()
                # Exclude classified Non-fuel/water, but keep valid zeros over fuel.
                values[non_fuel_mask] = nodata
                band.WriteArray(values)
            # GDAL ignores NoData during resampling. SFMS Insights adds the fuel classification separately.
            generate_web_optimized_cog(masked_path, output_path)

    logger.info("COG created at %s", output_path)
    return output_path
