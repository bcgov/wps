# -*- coding: utf-8 -*-
from pathlib import Path
import os
import matplotlib.patheffects as PathEffects
from matplotlib.patches import Rectangle

def get_project_root():
    """
    Robust project root finder
    """
    if "__file__" in globals():
        here = Path(__file__).resolve()
        # if this file is in src/, project root is src/..
        if here.parent.name == "src":
            return here.parent.parent
        # if in a subfolder under src/
        if "src" in [p.name for p in here.parents]:
            for p in here.parents:
                if p.name == "src":
                    return p.parent
        return here.parent

    cwd = Path(os.getcwd()).resolve()
    if cwd.name == "src":
        return cwd.parent
    if (cwd / "src").exists():
        return cwd
    return cwd


def add_panel_title(ax, text, loc="bl", fontsize=10):
    anchors = {
        "tl": (0.012, 0.988, "left",  "top"),
        "tr": (0.988, 0.988, "right", "top"),
        "bl": (0.012, 0.012, "left",  "bottom"),
        "br": (0.988, 0.012, "right", "bottom"),
    }
    x, y, ha, va = anchors[loc]
    t = ax.text(
        x, y, text, transform=ax.transAxes,
        ha=ha, va=va, fontsize=fontsize, fontweight="bold",
        color="black", zorder=2000,
        bbox=dict(boxstyle="square,pad=0.18", facecolor=(1, 1, 1),
                  edgecolor="black", linewidth=0.8),
    )
    t.set_path_effects([PathEffects.Normal()])
    return t


def add_valid_time_stamp(
    fig,
    text,
    loc="top",
    box_alpha=0.35,
    fontsize=14,
    height=0.04,
    facecolor="black",
    text_color="white",
    zorder=5000,
):
    y0 = 1.0 - height if loc == "top" else 0.0

    band = Rectangle(
        (0.0, y0), 1.0, height,
        transform=fig.transFigure,
        facecolor=facecolor,
        edgecolor="none",
        linewidth=0.0,
        alpha=box_alpha,
        zorder=zorder,
        clip_on=False,
    )
    fig.add_artist(band)

    t = fig.text(
        0.5, y0 + height / 2,
        text, ha="center", va="center",
        color=text_color, fontsize=fontsize, fontweight="bold",
        zorder=zorder + 1,
    )
    t.set_path_effects([
        PathEffects.Stroke(linewidth=2, foreground="black", alpha=0.25),
        PathEffects.Normal()
    ])
    return band, t


def apply_4panel_frames(fig, axes, add_outer_border=True):
    """
    Make GDPS and RDPS look identical
    """
    ax_list = [axes[0,0], axes[0,1], axes[1,0], axes[1,1]]

    for ax in ax_list:
        ax.set_aspect("auto")
        ax.set_anchor("C")
        ax.set_title("")

        # Some environments behave differently for GeoAxes spines,
        # so we use BOTH geo spine (if present) and patch edge.
        try:
            if "geo" in ax.spines:
                ax.spines["geo"].set_edgecolor("black")
                ax.spines["geo"].set_linewidth(1.0)
                ax.spines["geo"].set_visible(False)
        except Exception:
            pass

        ax.patch.set_edgecolor("black")
        ax.patch.set_linewidth(1.0)
        ax.patch.set_facecolor("none")

    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0, wspace=0.0, hspace=0.0)

    if add_outer_border:
        border = Rectangle(
            (0, 0), 1, 1,
            transform=fig.transFigure,
            fill=False,
            edgecolor="black",
            linewidth=2.0,
            zorder=1000,
            joinstyle="miter",
        )
        fig.add_artist(border)
        return border

    return None
