# -*- coding: utf-8 -*-
"""
Generate a 2x2 4-panel plot for RDPS (3-hourly).

Panels:
(1) RDPS 500 hPa Height + Abs Vorticity
(2) RDPS MSLP + 1000–500 Thickness
(3) RDPS 700 hPa Height + Layer-mean RH (850/700/500)
(4) RDPS 3h Accum PCPN + 250 hPa Jet

Assumes you already have these RDPS plotting modules (the ones we built):
- plot_500mb_rdps.py  -> plot_500hpa(cfg, ax=...), CFG_500
- plot_mslp_rdps.py   -> plot_mslp_thickness_rdps(cfg, ax=...), CFG_MSLP_RDPS
- plot_700mb_rdps.py  -> plot_700hpa_rdps(cfg, ax=...), CFG_700_RDPS
- plot_precip_rdps.py -> plot_pcpn3_rdps(cfg, ax=...), CFG_PCPN3H_RDPS

Directory structure (same as GDPS script):
data_hpfx/YYYYMMDD/HH/FFF/*.grib2

Notes:
- RDPS is curvilinear (2D lat/lon). Your RDPS plotters should use tricontour and ax.set_extent.
- This script builds the file paths and loops forecast hours.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from matplotlib.patches import Rectangle
import matplotlib.patheffects as PathEffects
import matplotlib.tri as mtri


# -----------------------------
# Import YOUR RDPS plotters
# -----------------------------
from plot_500mb_rdps import plot_500hpa, CFG_500 as CFG_500_RDPS
from plot_mslp_rdps import plot_mslp_thickness_rdps, CFG_MSLP_RDPS as CFG_MSLP_RDPS
from plot_700mb_rdps import plot_700hpa_rdps, CFG_700_RDPS as CFG_700_RDPS
from plot_precip_rdps import plot_pcpn3_rdps, PLOT_CONFIG_PCPN3_RDPS  as CFG_PCPN_RDPS


# -----------------------------
# File naming + cfg builders
# -----------------------------
def rdps_fname(init_ymd: str, init_hh: str, field: str, level: str | None, fh: int,
              grid: str = "RLatLon0.09") -> str:
    """
    RDPS filename:
    YYYYMMDDTHHZ_MSC_RDPS_<field>_<level?>_<grid>_PTFFFH.grib2
    If level is None/"" -> omit it (e.g., Pressure_MSL has no level token).
    """
    level_part = f"_{level}" if level else ""
    return f"{init_ymd}T{init_hh}Z_MSC_RDPS_{field}{level_part}_{grid}_PT{fh:03d}H.grib2"


def _valid_time_str(init_ymd: str, init_hh: str, fh: int) -> str:
    init_dt = datetime.strptime(f"{init_ymd}{init_hh}", "%Y%m%d%H")
    valid_dt = init_dt + timedelta(hours=int(fh))
    return f"F{fh:03d} Valid: {valid_dt:%a %Y-%m-%d %HZ}"


def build_cfgs_for_fh_rdps(init_ymd: str, init_hh: str, fh: int, data_root="data_hpfx"):
    """
    Build cfg dicts using HPFX directory structure:
    data_hpfx/YYYYMMDD/HH/FFF/*.grib2
    """
    data_root = Path(data_root)
    fh_dir = f"{fh:03d}"
    base_dir = data_root / init_ymd / init_hh / fh_dir

    # ---- 500 hPa ----
    cfg500 = CFG_500_RDPS.copy()
    cfg500["z500_grib"] = str(base_dir / rdps_fname(init_ymd, init_hh, "GeopotentialHeight", "IsbL-0500", fh))
    cfg500["vort_grib"] = str(base_dir / rdps_fname(init_ymd, init_hh, "AbsoluteVorticity", "IsbL-0500", fh))
    cfg500["valid_time_str"] = _valid_time_str(init_ymd, init_hh, fh)

    # ---- MSLP + thickness ----
    cfgmslp = CFG_MSLP_RDPS.copy()
    cfgmslp["mslp_grib"] = str(base_dir / rdps_fname(init_ymd, init_hh, "Pressure_MSL", None, fh))
    cfgmslp["thk_grib"]  = str(base_dir / rdps_fname(init_ymd, init_hh, "Thickness", "IsbL-1000to0500", fh))

    # ---- 700 hPa + RH layer mean ----
    cfg700 = CFG_700_RDPS.copy()
    cfg700["z700_grib"]  = str(base_dir / rdps_fname(init_ymd, init_hh, "GeopotentialHeight", "IsbL-0700", fh))
    cfg700["rh500_grib"] = str(base_dir / rdps_fname(init_ymd, init_hh, "RelativeHumidity", "IsbL-0500", fh))
    cfg700["rh700_grib"] = str(base_dir / rdps_fname(init_ymd, init_hh, "RelativeHumidity", "IsbL-0700", fh))
    cfg700["rh850_grib"] = str(base_dir / rdps_fname(init_ymd, init_hh, "RelativeHumidity", "IsbL-0850", fh))

    # ---- 3h precip + jet ----
    cfgpcpn = CFG_PCPN_RDPS.copy()
    cfgpcpn["jet_spd_grib"] = str(base_dir / rdps_fname(init_ymd, init_hh, "WindSpeed", "IsbL-0250", fh))

    if fh == 0:
        cfgpcpn["show_precip"] = False  # jet-only at analysis time
    else:
        cfgpcpn["show_precip"] = True
        # RDPS 3-hourly accumulation (adjust field token if your files differ)
        cfgpcpn["pcpn_grib"] = str(base_dir / rdps_fname(init_ymd, init_hh, "Precip-Accum3h", "Sfc", fh))

    return cfg500, cfgmslp, cfg700, cfgpcpn


# -----------------------------
# Small in-panel title + valid stamp
# -----------------------------
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
                  edgecolor="black", linewidth=0.8)
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


def get_project_root():
    if "__file__" in globals():
        return Path(__file__).resolve().parents[1]
    cwd = Path(os.getcwd()).resolve()
    if cwd.name == "src":
        return cwd.parent
    return cwd


# -----------------------------
# Single-figure maker
# -----------------------------
def make_4panel_rdps(
    cfg500,
    cfgmslp,
    cfg700,
    cfgpcpn,
    figsize=(11.8, 10),
    dpi=300,
    outname="RDPS_4panel.png",
    output_dir="outputs",
):
    ROOT = get_project_root()
    outdir = ROOT / output_dir
    outdir.mkdir(exist_ok=True)

    proj = ccrs.LambertConformal(
        central_longitude=cfg500.get("central_longitude", -130.0),
        central_latitude=cfg500.get("central_latitude", 50.0),
    )

    fig, axes = plt.subplots(
        2, 2,
        figsize=figsize,
        dpi=dpi,
        subplot_kw={"projection": proj},
    )

    ax500, axmslp = axes[0, 0], axes[0, 1]
    ax700, axpcpn = axes[1, 0], axes[1, 1]

    plot_500hpa(cfg500, ax=ax500)
    add_panel_title(ax500, "500 hPa Height + Abs Vorticity", loc="bl")

    plot_mslp_thickness_rdps(cfgmslp, ax=axmslp)
    add_panel_title(axmslp, "MSLP + 1000–500 Thickness", loc="bl")

    plot_700hpa_rdps(cfg700, ax=ax700)
    add_panel_title(ax700, "700 hPa Height + RH (850/700/500)", loc="bl")

    plot_pcpn3_rdps(cfgpcpn, ax=axpcpn)
    add_panel_title(axpcpn, "3H PCPN + 250 hPa Jet" if cfgpcpn.get("show_precip", True) else "250 hPa Jet", loc="bl")

    # ---- Frames + no gaps (fix missing boundary) ----
    for ax in [ax500, axmslp, ax700, axpcpn]:
        ax.set_aspect("auto")
        ax.set_anchor("C")
        ax.set_title("")

        # Force the GeoAxes frame to draw fully
        try:
            ax.spines["geo"].set_visible(True)
            ax.spines["geo"].set_edgecolor("black")
            ax.spines["geo"].set_linewidth(1.0)
            ax.spines["geo"].set_zorder(10000)
        except Exception:
            pass

        # Also keep a patch edge as a backup border
        ax.patch.set_edgecolor("black")
        ax.patch.set_linewidth(1.0)
        ax.patch.set_facecolor("none")

    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0, wspace=0.0, hspace=0.0)

    # outer border
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

    valid_text = cfg500.get("valid_time_str", "")
    if valid_text:
        add_valid_time_stamp(fig, valid_text, height=0.04, fontsize=14)

    outpath = outdir / outname
    fig.savefig(outpath, dpi=dpi, bbox_inches=None, pad_inches=0.0, facecolor="white")
    plt.close(fig)
    print("Saved:", outpath)
    return outpath


# -----------------------------
# Batch runner (3-hourly loop)
# -----------------------------
def batch_make_4panel_rdps(
    init_ymd: str,
    init_hh: str,
    fstart: int = 0,
    fend: int = 84,
    step: int = 3,
    data_dir: str = "data_hpfx",
    output_dir: str = "outputs",
    figsize=(11.8, 10),
    dpi: int = 300,
    skip_missing: bool = True,
):
    """
    Makes RDPS maps every 3h.
    """
    ROOT = get_project_root()
    data_dir_path = ROOT / data_dir

    for fh in range(int(fstart), int(fend) + 1, int(step)):
        cfg500, cfgmslp, cfg700, cfgpcpn = build_cfgs_for_fh_rdps(init_ymd, init_hh, fh, data_root=data_dir_path)

        needed = [
            cfg500["z500_grib"], cfg500["vort_grib"],
            cfgmslp["mslp_grib"], cfgmslp["thk_grib"],
            cfg700["z700_grib"], cfg700["rh500_grib"], cfg700["rh700_grib"], cfg700["rh850_grib"],
        ]

        if cfgpcpn.get("show_precip", True):
            needed.append(cfgpcpn["pcpn_grib"])
        if cfgpcpn.get("show_jet_core", True):
            needed.append(cfgpcpn["jet_spd_grib"])

        missing = [p for p in needed if not Path(p).exists()]
        if missing:
            msg = f"[SKIP F{fh:03d}] missing {len(missing)} files, e.g. {missing[0]}"
            if skip_missing:
                print(msg)
                continue
            raise FileNotFoundError(msg)

        outname = f"RDPS_{init_ymd}T{init_hh}Z_F{fh:03d}_4panel.png"
        make_4panel_rdps(
            cfg500, cfgmslp, cfg700, cfgpcpn,
            figsize=figsize,
            dpi=dpi,
            outname=outname,
            output_dir=output_dir,
        )


if __name__ == "__main__":
    # Example
    batch_make_4panel_rdps(
        init_ymd="20260112",
        init_hh="12",
        fstart=0,
        fend=84,
        step=3,
        data_dir="data_hpfx",
        output_dir="outputs/RDPS_20260112T12Z",
        figsize=(11.8, 10),
        dpi=300,
        skip_missing=True,
    )
