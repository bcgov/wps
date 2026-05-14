from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def create_sfms_scatterplot(
    x_data: np.ndarray,
    y_data: np.ndarray,
    x_label: str = None,
    y_label: str = None,
    title: str = None,
    out_dir: str = None,
    out_name: str = None,
    show_trend_line: bool = False # Show a basic y = mx + b trend line
):
    plt.figure(figsize=(8, 5))
    plt.scatter(x_data, y_data, s=30, color="#1f77b4", alpha=0.8, label="Data")
    if show_trend_line:
        z = np.polyfit(x_data, y_data, 1)
        p = np.poly1d(z)
        plt.plot(x_data, p(x_data), "r--", label=f'Linear Trend Line (y={z[0]:.2f}x + {z[1]:.2f})')

    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if out_dir is None:
        plt.show()
    else:
        Path(out_dir).mkdir(exist_ok=True)
        out_path = f"{out_dir}/{out_name}"
        plt.savefig(out_path, dpi=150)
        print(f"Saved scatterplot to {out_path}")
    plt.close()
