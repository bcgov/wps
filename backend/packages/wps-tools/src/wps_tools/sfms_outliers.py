import argparse
import numpy as np
from osgeo import gdal
import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(
        description="Generate map showing outlier differences between two SFMS raster files"
    )
    parser.add_argument("generated", help="Path to generated raster file")
    parser.add_argument("reference", help="Path to reference raster file")
    parser.add_argument(
        "-o",
        "--output",
        default="outliers_map.png",
        help="Output image path (default: outliers_map.png)",
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=5.0,
        help="Threshold for outliers (default: 5.0)",
    )
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

    # Mask to only show outliers
    outliers = np.where(np.abs(diff) > args.threshold, diff, np.nan)

    # Compute range for symmetric colorbar
    diff_abs_max = np.nanmax(np.abs(diff))

    _, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Left: full difference map for context
    ax1 = axes[0]
    im1 = ax1.imshow(diff, cmap="RdBu", vmin=-diff_abs_max, vmax=diff_abs_max)
    ax1.set_title("All Differences (Gen - Ref)")
    plt.colorbar(im1, ax=ax1)

    # Right: only outliers
    ax2 = axes[1]
    im2 = ax2.imshow(outliers, cmap="RdBu", vmin=-diff_abs_max, vmax=diff_abs_max)
    ax2.set_title(f"Outliers Only (|diff| > {args.threshold})")
    plt.colorbar(im2, ax=ax2)

    # Count outliers
    num_outliers = int(np.sum(~np.isnan(outliers)))
    total_valid = int(np.sum(both_valid))
    pct = 100 * num_outliers / total_valid
    ax2.text(
        0.02,
        0.98,
        f"Outliers: {num_outliers:,} pixels ({pct:.2f}%)",
        transform=ax2.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
    )

    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f"Saved outliers map to {args.output}")


if __name__ == "__main__":
    main()
