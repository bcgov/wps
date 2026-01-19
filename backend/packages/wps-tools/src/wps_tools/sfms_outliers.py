import numpy as np
import matplotlib
from wps_tools.sfms_raster_input_parser import parse_input, create_parser

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt


def main():
    parser = create_parser(
        description="Generate map showing outlier differences between two SFMS raster files"
    )

    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=5.0,
        help="Threshold for outliers (default: 5.0)",
    )

    _, _, valid1, valid2, diff, args = parse_input(parser)

    both_valid = valid1 & valid2

    # Mask to only show outliers
    outliers = np.where(np.abs(diff) > args.threshold, diff, np.nan)

    # Compute range for symmetric colorbar
    diff_abs_max = np.nanmax(np.abs(diff))

    _, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Left: full difference map for context
    ax1 = axes[0]
    im1 = ax1.imshow(diff, cmap="RdBu_r", vmin=-diff_abs_max, vmax=diff_abs_max)
    ax1.set_title("All Differences (Gen - Ref)")
    plt.colorbar(im1, ax=ax1)

    # Right: only outliers
    ax2 = axes[1]
    im2 = ax2.imshow(outliers, cmap="RdBu_r", vmin=-diff_abs_max, vmax=diff_abs_max)
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
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.8},
    )

    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f"Saved outliers map to {args.output}")


if __name__ == "__main__":
    main()
