import argparse
import numpy as np
from osgeo import gdal


def create_parser(description: str):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("generated", help="Path to generated raster file")
    parser.add_argument("reference", help="Path to reference raster file")
    parser.add_argument(
        "-o",
        "--output",
        default="temp_comparison.png",
        help="Output image path (default: temp_comparison.png)",
    )
    return parser


def parse_input(parser: argparse.ArgumentParser):
    args = parser.parse_args()

    ds1: gdal.Dataset = gdal.Open(args.generated)
    ds2: gdal.Dataset = gdal.Open(args.reference)

    if ds1 is None:
        raise FileNotFoundError(f"Could not open generated file: {args.generated}")
    if ds2 is None:
        raise FileNotFoundError(f"Could not open reference file: {args.reference}")

    data1 = ds1.GetRasterBand(1).ReadAsArray()
    data2 = ds2.GetRasterBand(1).ReadAsArray()

    nodata1 = ds1.GetRasterBand(1).GetNoDataValue()
    nodata2 = ds2.GetRasterBand(1).GetNoDataValue()

    valid1 = data1 != nodata1 if nodata1 is not None else np.ones_like(data1, dtype=bool)
    valid2 = data2 != nodata2 if nodata2 is not None else np.ones_like(data2, dtype=bool)

    both_valid = valid1 & valid2

    diff = np.where(both_valid, data1 - data2, np.nan)

    return data1, data2, valid1, valid2, diff, args
