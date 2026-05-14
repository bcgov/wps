import matplotlib
import numpy as np
from pathlib import Path

from wps_tools.sfms_raster_input_parser import create_parser, parse_input

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt


def create_sfms_histogram(data: np.ndarray, x_label: str, y_label: str, title: str, out_path: str):
    _, ax = plt.subplots(figsize=(10, 6))
    ax.hist(data, bins=100, edgecolor="black", alpha=0.7)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.axvline(x=0, color="red", linestyle="--", label="Zero difference")

    # Add stats
    mean_diff = np.nanmean(data)
    std_diff = np.nanstd(data)
    ax.axvline(x=mean_diff, color="green", linestyle="-", label=f"Mean: {mean_diff:.2f}")
    ax.legend()

    # Add text box with stats
    stats_text = f"Mean: {mean_diff:.2f}\nStd: {std_diff:.2f}\nMin: {np.nanmin(data):.2f}\nMax: {np.nanmax(data):.2f}"
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
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Saved histogram to {out_path}")


def main():
    _, _, _, _, diff, args = parse_input(
        create_parser(description="Generate histogram of differences between two SFMS raster files")
    )
    generated_name = Path(args.generated).name
    reference_name = Path(args.reference).name
    x_label = "Difference (Generated - Reference)"
    y_label = "Pixel Count"
    title = f"Histogram of Raster Differences\n{generated_name} - {reference_name}"

    create_sfms_histogram(diff, x_label, y_label, title, args.output)


if __name__ == "__main__":
    main()
