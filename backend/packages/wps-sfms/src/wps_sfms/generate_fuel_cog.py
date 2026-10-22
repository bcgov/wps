"""convert a fuel TIFF to an EPSG:3857 COG with SFMS nodata.

Run from backend/. Output defaults to <input_stem>_3857_cog.tif beside the input;
use --output to choose another path.

Example:
    uv run python -m wps_sfms.generate_fuel_cog \
        --input ../web/apps/wps-web/src/features/sfmsInsights/components/map/fbp2025_v2.tif
"""

import argparse
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from osgeo import gdal
from wps_sfms.interpolation.common import SFMS_NO_DATA

logger = logging.getLogger(__name__)


def reproject_raster_to_3857(input_path: str, output_path: str) -> str:
    """reproject using nearest neighbour to preserve categorical fuel codes."""
    with gdal.ExceptionMgr(), gdal.Open(input_path) as source:
        transform = source.GetGeoTransform()
        gdal.Warp(
            output_path,
            source,
            dstSRS="EPSG:3857",
            dstNodata=float(np.float32(SFMS_NO_DATA)),
            # float32 can represent the SFMS nodata value even for integer inputs
            outputType=gdal.GDT_Float32,
            xRes=abs(transform[1]),
            yRes=abs(transform[5]),
            resampleAlg=gdal.GRA_NearestNeighbour,
            format="GTiff",
        ).Close()

    logger.info("Reprojection complete. Output saved to: %s", output_path)
    return output_path


def generate_cloud_optimized_geotiff(input_path: str, output_path: str) -> None:
    """create a COG with nearest neighbour overviews for categorical fuel codes."""
    options = ["COMPRESS=LZW", "OVERVIEWS=IGNORE_EXISTING", "RESAMPLING=NEAREST"]
    with gdal.ExceptionMgr(), gdal.Open(input_path) as source:
        gdal.GetDriverByName("COG").CreateCopy(output_path, source, options=options).Close()
    logger.info("COG created at %s", output_path)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Convert a fuel TIFF to an EPSG:3857 COG")
    parser.add_argument("--input", required=True, type=Path, help="Input TIFF path")
    parser.add_argument(
        "--output", type=Path, help="Output path (default: <input_stem>_3857_cog.tif)"
    )
    args = parser.parse_args(argv)
    output = args.output or args.input.with_name(f"{args.input.stem}_3857_cog.tif")
    if args.input.resolve() == output.resolve():
        parser.error("Input and output paths must differ")

    logging.basicConfig(level=logging.INFO)
    try:
        with TemporaryDirectory() as temp_dir:
            reprojected = str(Path(temp_dir) / "fuel_grid_reprojected.tif")
            reproject_raster_to_3857(str(args.input), reprojected)
            generate_cloud_optimized_geotiff(reprojected, str(output))
    except (RuntimeError, OSError) as error:
        parser.exit(1, f"Conversion failed: {error}\n")


if __name__ == "__main__":
    main()
