# -*- coding: utf-8 -*-
"""
Generate a 2x2 4-panel plot for operational GEM regional (RDPS 10km, 3-hourly).

This is the GEM/CMC *operational* naming version of your existing plot_4panel_rdps.py.

Panels (same layout/logic as your RDPS script):
(1) 500 hPa Height + Abs Vorticity
(2) MSLP + 1000–500 Thickness
(3) 700 hPa Height + Layer-mean RH (850/700/500)
(4) 3h Accum PCPN + 250 hPa Jet

Expected local directory structure (same as your other workflows):
  data/YYYYMMDD/CC/FFF/*.grib2

Where files are downloaded from (example):
  https://dd.weather.gc.ca/YYYYMMDD/WXO-DD/model_gem_regional/10km/grib2/CC/FFF/

Notes:
- This script ONLY builds paths + loops FHs.
- It does NOT modify any subplot plotters.
- If one token differs (e.g., vorticity var name), adjust ONLY the regex finders below.

Uses the existing RDPS plotters (UNCHANGED):
- plot_500mb_rdps.py  -> plot_500hpa(cfg, ax=...), CFG_500
- plot_mslp_rdps.py   -> plot_mslp_thickness_rdps(cfg, ax=...), CFG_MSLP_RDPS
- plot_700mb_rdps.py  -> plot_700hpa_rdps(cfg, ax=...), CFG_700_RDPS
- plot_precip_rdps.py -> plot_pcpn3_rdps(cfg, ax=...), CFG_PCPN3H_RDPS
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import argparse

import cartopy.crs as ccrs
import matplotlib.pyplot as plt

# Panel layout helpers (unchanged)
from panel_layout import (
    add_panel_title,
    add_valid_time_stamp,
    apply_4panel_frames,
    get_project_root,
)
from plot_500mb_rdps import CFG_500 as CFG_500_RDPS

# -----------------------------
# Import RDPS plotters (UNCHANGED)
# -----------------------------
from plot_500mb_rdps import plot_500hpa
from plot_700mb_rdps import CFG_700_RDPS as CFG_700_RDPS
from plot_700mb_rdps import plot_700hpa_rdps
from plot_mslp_rdps import CFG_MSLP_RDPS as CFG_MSLP_RDPS
from plot_mslp_rdps import plot_mslp_thickness_rdps
from plot_precip_rdps import PLOT_CONFIG_PCPN3_RDPS as CFG_PCPN_RDPS
from plot_precip_rdps import plot_pcpn3_rdps


# -----------------------------
# Time string
# -----------------------------
def _valid_time_str(init_ymd: str, init_hh: str, fh: int) -> str:
    init_dt = datetime.strptime(f"{init_ymd}{init_hh}", "%Y%m%d%H")
    valid_dt = init_dt + timedelta(hours=int(fh))
    return f"F{fh:03d} Valid: {valid_dt:%a %Y-%m-%d %HZ}"


# -----------------------------
# File discovery helpers
# -----------------------------
def _list_grib2(folder: Path):
    if not folder.exists():
        return []
    return sorted([p for p in folder.iterdir() if p.is_file() and p.name.endswith(".grib2")])


def _find_one(folder: Path, patterns: list[str], *, required: bool = True) -> Path | None:
    """
    Find one GRIB2 file in folder matching ANY regex pattern (uses re.search).
    Returns the first match by sorted filename.

    If not found and required=True -> raises with a helpful folder listing.
    """
    files = _list_grib2(folder)
    if not files:
        if required:
            raise FileNotFoundError(f"No .grib2 files found in: {folder}")
        return None

    rx = [re.compile(p) for p in patterns]
    hits = []
    for f in files:
        name = f.name
        if any(r.search(name) for r in rx):  # IMPORTANT: search, not match
            hits.append(f)

    if not hits:
        if required:
            example = "\n    ".join([p.name for p in files[:40]])
            raise FileNotFoundError(
                f"Missing required field in folder:\n  {folder}\n"
                f"Tried patterns:\n  - " + "\n  - ".join(patterns) + "\n"
                f"Files present (first 40):\n    {example}\n"
            )
        return None

    return hits[0]


# -----------------------------
# Pattern sets: experiment + operational
# -----------------------------
# These are deliberately broad enough to survive small naming variations.
PAT = {
    # 500 hPa height
    "z500": [
        r"_GeopotentialHeight_IsbL-0500_.*\.grib2$",
    ],
    # 500 hPa vorticity (prefer ABSV; fall back RELV)
    "vort500": [
        r"_AbsoluteVorticity_IsbL-0500_.*\.grib2$",
        r"_RelativeVorticity_IsbL-0500_.*\.grib2$",
    ],
    # MSLP
    "mslp": [
        r"_Pressure_MSL_.*\.grib2$",
    ],
    # thickness (1000–500)
    "thk1000_500": [
        r"_Thickness_IsbL-1000to0500_.*\.grib2$",
    ],
    # 700 hPa height
    "z700": [
        r"_GeopotentialHeight_IsbL-0700_.*\.grib2$",
    ],
    # RH levels
    "rh500": [
        r"_RelativeHumidity_IsbL-0500_.*\.grib2$",
    ],
    "rh700": [
        r"_RelativeHumidity_IsbL-0700_.*\.grib2$",
    ],
    "rh850": [
        r"_RelativeHumidity_IsbL-0850_.*\.grib2$",
    ],
    # 3h precip
    "pcpn3": [
        r"_Precip-Accum3h_.*\.grib2$",
    ],
    # 250 hPa wind speed for jet (only if the precip plotter requests it)
    "wspd250": [
        r"_WindSpeed_IsbL-0250_.*\.grib2$",
        r"CMC_reg_(UGRD|VGRD)_ISBL_250_.*\.grib2$",
    ],
}


# -----------------------------
# CFG builder (discovery-based)
# -----------------------------
def build_cfgs_for_fh(init_ymd: str, init_hh: str, fh: int, data_root="data_hpx"):
    """
    Builds cfg dicts by DISCOVERING files within:
      data_root/YYYYMMDD/HH/FFF/*.grib2
    """
    data_root = Path(data_root)
    base_dir = data_root / init_ymd / init_hh / f"{fh:03d}"

    cfg500 = CFG_500_RDPS.copy()
    cfg500["z500_grib"] = str(_find_one(base_dir, PAT["z500"]))
    cfg500["vort_grib"] = str(_find_one(base_dir, PAT["vort500"]))
    cfg500["valid_time_str"] = _valid_time_str(init_ymd, init_hh, fh)

    cfgmslp = CFG_MSLP_RDPS.copy()
    cfgmslp["mslp_grib"] = str(_find_one(base_dir, PAT["mslp"]))
    cfgmslp["thk_grib"] = str(_find_one(base_dir, PAT["thk1000_500"]))

    cfg700 = CFG_700_RDPS.copy()
    cfg700["z700_grib"] = str(_find_one(base_dir, PAT["z700"]))
    cfg700["rh500_grib"] = str(_find_one(base_dir, PAT["rh500"]))
    cfg700["rh700_grib"] = str(_find_one(base_dir, PAT["rh700"]))
    cfg700["rh850_grib"] = str(_find_one(base_dir, PAT["rh850"]))

    cfgpcpn = CFG_PCPN_RDPS.copy()
    if fh == 0:
        cfgpcpn["show_precip"] = False
    else:
        cfgpcpn["show_precip"] = True
        cfgpcpn["pcpn_grib"] = str(_find_one(base_dir, PAT["pcpn3"]))

    # Only resolve jet if your plotter asks for it
    if cfgpcpn.get("show_jet_core", False):
        cfgpcpn["jet_spd_grib"] = str(_find_one(base_dir, PAT["wspd250"], required=False) or "")

    return cfg500, cfgmslp, cfg700, cfgpcpn


# -----------------------------
# Single-figure maker
# -----------------------------
def make_4panel(
    cfg500,
    cfgmslp,
    cfg700,
    cfgpcpn,
    figsize=(11.8, 10),
    dpi=300,
    outname="GEMREG_4panel.png",
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
        2,
        2,
        figsize=figsize,
        dpi=dpi,
        subplot_kw={"projection": proj},
    )

    ax500, axmslp = axes[0, 0], axes[0, 1]
    ax700, axpcpn = axes[1, 0], axes[1, 1]

    plot_500hpa(cfg500, ax=ax500)
    add_panel_title(ax500, "500 hPa Height + Absolute Vorticity (10⁻⁵ s⁻¹)", loc="bl")

    plot_mslp_thickness_rdps(cfgmslp, ax=axmslp)
    add_panel_title(axmslp, "MSLP + 1000–500 Thickness", loc="bl")

    plot_700hpa_rdps(cfg700, ax=ax700)
    add_panel_title(ax700, "700 hPa Height + 850–500 Relative Humidity", loc="bl")

    plot_pcpn3_rdps(cfgpcpn, ax=axpcpn)
    add_panel_title(
        axpcpn, "3H PCPN" if cfgpcpn.get("show_precip", True) else "No PCPN at 00H", loc="bl"
    )

    apply_4panel_frames(fig, axes, add_outer_border=True)

    valid_text = cfg500.get("valid_time_str", "")
    if valid_text:
        add_valid_time_stamp(fig, valid_text, height=0.04, fontsize=14)

    outpath = outdir / outname
    fig.savefig(outpath, dpi=dpi, bbox_inches=None, pad_inches=0.0, facecolor="white")
    plt.close(fig)
    print("Saved:", outpath)
    return outpath


# -----------------------------
# Batch runner
# -----------------------------
def batch_make_4panel_gem_regional(
    init_ymd: str,
    init_hh: str,
    fstart: int = 0,
    fend: int = 84,
    step: int = 3,
    data_dir: str = "data_hpx",
    output_dir: str = "outputs",
    figsize=(11.8, 10),
    dpi: int = 300,
    skip_missing: bool = True,
):
    ROOT = get_project_root()
    data_dir_path = ROOT / data_dir
    print("Data root:", data_dir_path)

    for fh in range(int(fstart), int(fend) + 1, int(step)):
        try:
            cfg500, cfgmslp, cfg700, cfgpcpn = build_cfgs_for_fh(
                init_ymd, init_hh, fh, data_root=data_dir_path
            )
        except FileNotFoundError as e:
            msg = f"[SKIP F{fh:03d}] {e}"
            if skip_missing:
                print(msg)
                continue
            raise

        outname = f"GEMREG_{init_ymd}T{init_hh}Z_F{fh:03d}_4panel.png"
        make_4panel(
            cfg500,
            cfgmslp,
            cfg700,
            cfgpcpn,
            figsize=figsize,
            dpi=dpi,
            outname=outname,
            output_dir=output_dir,
        )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", default="", help="init time like 20260120T00Z (UTC)")
    ap.add_argument("--date", default="", help="UTC date YYYYMMDD (alternative to --init)")
    ap.add_argument("--cycle", default="", help="cycle HH (00 or 12) (alternative to --init)")
    ap.add_argument(
        "--auto", action="store_true", help="auto-pick latest available init in data_dir"
    )
    ap.add_argument("--lookback_days", type=int, default=2, help="for --auto, search back N days")
    ap.add_argument("--data_dir", default="data_hpx")
    ap.add_argument("--out_base", default="outputs")  # base output folder
    ap.add_argument("--fstart", type=int, default=0)
    ap.add_argument("--fend", type=int, default=84)
    ap.add_argument("--step", type=int, default=3)
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()

    ROOT = get_project_root()
    data_root = ROOT / args.data_dir

    def parse_init(s: str):
        # "20260120T00Z" -> ("20260120","00")
        s = s.strip().upper()
        if "T" in s:
            ymd, rest = s.split("T", 1)
            hh = rest.replace("Z", "")[:2]
            return ymd, hh
        raise ValueError("Bad --init format, expected YYYYMMDDTHHZ")

    # ---- decide init_ymd / init_hh ----
    if args.auto:
        # search newest existing folder: data_hpx/YYYYMMDD/HH/
        candidates = []
        now = datetime.utcnow()
        for dd in range(args.lookback_days + 1):
            d = (now - timedelta(days=dd)).strftime("%Y%m%d")
            for hh in ["12", "00"]:  # prefer 12 then 00 if both exist on same day
                if (data_root / d / hh).exists():
                    # rank by datetime
                    dt = datetime.strptime(d + hh, "%Y%m%d%H")
                    candidates.append((dt, d, hh))
        if not candidates:
            raise FileNotFoundError(f"No init folders found under: {data_root}")
        candidates.sort()
        init_dt, init_ymd, init_hh = candidates[-1]
    elif args.init.strip():
        init_ymd, init_hh = parse_init(args.init)
    else:
        # use --date + --cycle
        if not args.date or not args.cycle:
            raise ValueError("Provide either --init, or (--date and --cycle), or use --auto.")
        init_ymd, init_hh = args.date.strip(), args.cycle.strip()

    init_tag = f"{init_ymd}T{init_hh}Z"
    output_dir = f"{args.out_base}/GEMREG_{init_tag}"

    batch_make_4panel_gem_regional(
        init_ymd=init_ymd,
        init_hh=init_hh,
        fstart=args.fstart,
        fend=args.fend,
        step=args.step,
        data_dir=args.data_dir,
        output_dir=output_dir,
        figsize=(11.8, 10),
        dpi=args.dpi,
        skip_missing=True,
    )
    # Example
    # batch_make_4panel_gem_regional(
    #     init_ymd="20260220",
    #     init_hh="12",
    #     fstart=0,
    #     fend=6,
    #     step=3,
    #     data_dir="data_hpx",
    #     output_dir="outputs/GEMREG_20260220T12Z",
    #     figsize=(11.8, 10),
    #     dpi=300,
    #     skip_missing=True,
    # )
