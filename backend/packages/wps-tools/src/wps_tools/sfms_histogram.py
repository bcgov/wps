import argparse
import numpy as np
from osgeo import gdal
import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(
        description="Generate histogram of differences between two SFMS raster files"
    )
    parser.add_argument("generated", help="Path to generated raster file")
    parser.add_argument("reference", help="Path to reference raster file")
    parser.add_argument(
        "-o",
        "--output",
        default="diff_histogram.png",
        help="Output image path (default: diff_histogram.png)",
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
    diff = data1[both_valid] - data2[both_valid]

    _, ax = plt.subplots(figsize=(10, 6))
    ax.hist(diff, bins=100, edgecolor="black", alpha=0.7)
    ax.set_xlabel("Difference (Generated - Reference)")
    ax.set_ylabel("Pixel Count")
    ax.set_title("Histogram of Raster Differences")
    ax.axvline(x=0, color="red", linestyle="--", label="Zero difference")

    # Add stats
    mean_diff = np.mean(diff)
    std_diff = np.std(diff)
    ax.axvline(x=mean_diff, color="green", linestyle="-", label=f"Mean: {mean_diff:.2f}")
    ax.legend()

    # Add text box with stats
    stats_text = f"Mean: {mean_diff:.2f}\nStd: {std_diff:.2f}\nMin: {np.min(diff):.2f}\nMax: {np.max(diff):.2f}"
    ax.text(
        0.95,
        0.95,
        stats_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f"Saved histogram to {args.output}")


if __name__ == "__main__":
    main()
