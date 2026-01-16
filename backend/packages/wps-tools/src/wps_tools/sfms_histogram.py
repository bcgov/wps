import numpy as np
import matplotlib
from wps_tools.sfms_raster_input_parser import parse_input, create_parser

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt


def main():
    _, _, _, _, diff, args = parse_input(
        create_parser(description="Generate histogram of differences between two SFMS raster files")
    )

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
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5},
    )

    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f"Saved histogram to {args.output}")


if __name__ == "__main__":
    main()
