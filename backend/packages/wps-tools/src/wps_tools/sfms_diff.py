import argparse
import numpy as np
from osgeo import gdal
import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description="Compare two SFMS raster files and generate a difference image")
    parser.add_argument("generated", help="Path to generated raster file")
    parser.add_argument("reference", help="Path to reference raster file")
    parser.add_argument("-o", "--output", default="temp_comparison.png", help="Output image path (default: temp_comparison.png)")
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

    # Compute value ranges from valid data
    valid_data1 = data1[valid1]
    valid_data2 = data2[valid2]
    data_min = min(np.nanmin(valid_data1), np.nanmin(valid_data2))
    data_max = max(np.nanmax(valid_data1), np.nanmax(valid_data2))

    valid_diff = diff[~np.isnan(diff)]
    diff_abs_max = np.nanmax(np.abs(valid_diff)) if len(valid_diff) > 0 else 1

    # Create figure showing difference
    _, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Generated
    ax1 = axes[0]
    im1 = ax1.imshow(np.where(valid1, data1, np.nan), cmap="coolwarm", vmin=data_min, vmax=data_max)
    ax1.set_title("Generated")
    plt.colorbar(im1, ax=ax1)

    # Reference
    ax2 = axes[1]
    im2 = ax2.imshow(np.where(valid2, data2, np.nan), cmap="coolwarm", vmin=data_min, vmax=data_max)
    ax2.set_title("Reference")
    plt.colorbar(im2, ax=ax2)

    # Difference
    ax3 = axes[2]
    im3 = ax3.imshow(diff, cmap="RdBu", vmin=-diff_abs_max, vmax=diff_abs_max)
    ax3.set_title("Difference (Gen - Ref)")
    plt.colorbar(im3, ax=ax3)

    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f"Saved comparison image to {args.output}")


if __name__ == "__main__":
    main()
