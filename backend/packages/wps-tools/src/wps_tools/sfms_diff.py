import numpy as np
import matplotlib
from wps_tools.sfms_raster_input_parser import parse_input, create_parser

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt


def main():
    data1, data2, valid1, valid2, diff, args = parse_input(
        create_parser(description="Compare two SFMS raster files and generate a difference image")
    )

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
