# -*- coding: utf-8 -*-
"""
Generate a 2x2 4-panel plot for MANY forecast hours (6/12-hourly out to 10 days).

Key idea:
- Do NOT construct filenames.
- Instead, for each forecast-hour folder, *discover* the correct GRIB2 file by matching patterns.
- This avoids changing each subplot script when file naming conventions change (experiment vs operational).
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
import time
import matplotlib
matplotlib.use("Agg")
import argparse

import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# -----------------------------
# Import GDPS plotters (UNCHANGED)
# -----------------------------
from plot_500mb import plot_500hpa, CFG_500 as CFG_500
from plot_mslp import plot_mslp_thickness, CFG_MSLP as CFG_MSLP
from plot_700mb import plot_700hpa, CFG_700 as CFG_700
from plot_precip import plot_pcpn12, PLOT_CONFIG_PCPN12 as CFG_PCPN


# -----------------------------
# Import the panel settings
# -----------------------------
from panel_layout import (
    get_project_root,
    add_panel_title,
    add_valid_time_stamp,
    apply_4panel_frames,
)

import re


# -----------------------------
# Time string
# -----------------------------
def _valid_time_str(init_ymd: str, init_hh: str, fh: int) -> str:
    """
    Build "F036 Valid: Tue 2025-12-30 00Z" (UTC)
    """
    init_dt = datetime.strptime(f"{init_ymd}{init_hh}", "%Y%m%d%H")
    valid_dt = init_dt + timedelta(hours=int(fh))
    return f"F{fh:03d} Valid: {valid_dt:%a %Y-%m-%d %HZ}"


# -----------------------------
# File discovery (NEW)
# -----------------------------
def _list_grib2(folder: Path):
    if not folder.exists():
        return []
    return sorted([p for p in folder.iterdir() if p.is_file() and p.name.endswith(".grib2")])


def _find_one(folder: Path, patterns: list[str], *, required: bool = True) -> Path | None:
    """
    Find exactly one GRIB2 file in folder matching ANY of the regex patterns.
    Returns the first match by sorted filename.

    patterns: list of regex strings (case-sensitive)
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
        if any(r.search(name) for r in rx):
            hits.append(f)

    if not hits:
        if required:
            example = "\n    ".join([p.name for p in files[:20]])
            raise FileNotFoundError(
                f"Missing required field in folder:\n  {folder}\n"
                f"Tried patterns:\n  - " + "\n  - ".join(patterns) + "\n"
                f"Files present (first 20):\n    {example}\n"
            )
        return None

    return hits[0]


# -----------------------------
# Pattern sets: experiment + operational
# -----------------------------
PAT = {
    # 500 hPa
    "z500": [
        r"_GeopotentialHeight_IsbL-0500_.*\.grib2$",
        r"^CMC_glb_HGT_ISBL_500_.*\.grib2$",
    ],
    "rv500": [
        r"_RelativeVorticity_IsbL-0500_.*\.grib2$",
        r"^CMC_glb_RELV_ISBL_500_.*\.grib2$",
    ],

    # MSLP + thickness
    "mslp": [
        r"_Pressure_MSL_.*\.grib2$",
        r"^CMC_glb_PRMSL_MSL_0_.*\.grib2$",
    ],
    "thk1000_500": [
        r"_Thickness_IsbL-1000to0500_.*\.grib2$",
        r"^CMC_glb_HGT_ISBY_1000-500_.*\.grib2$",
    ],

    # 700 hPa + RH (your plot_700mb expects rh500/rh700/rh850 as separate files)
    "z700": [
        r"_GeopotentialHeight_IsbL-0700_.*\.grib2$",
        r"^CMC_glb_HGT_ISBL_700_.*\.grib2$",
    ],
    "rh500": [
        r"_RelativeHumidity_IsbL-0500_.*\.grib2$",
        r"^CMC_glb_RH_ISBL_500_.*\.grib2$",
    ],
    "rh700": [
        r"_RelativeHumidity_IsbL-0700_.*\.grib2$",
        r"^CMC_glb_RH_ISBL_700_.*\.grib2$",
    ],
    "rh850": [
        r"_RelativeHumidity_IsbL-0850_.*\.grib2$",
        r"^CMC_glb_RH_ISBL_850_.*\.grib2$",
    ],

    # precip (your plot_precip uses "pcpn_grib")
    # This catches both old "Precip-Accum12h" and operational "APCP-Accum12h_SFC_0_"
    "pcpn": [
        r"_Precip-Accum12h_Sfc_.*\.grib2$",
        r"^CMC_glb_APCP-Accum12h_SFC_0_.*\.grib2$",
    ],

    # jet speed (ONLY needed if cfgpcpn["show_jet_core"] == True in plot_precip)
    # Keep as-is: if you later need jet again and you have windspeed product, this will find it.
    "wspd250": [
        r"_WindSpeed_IsbL-0250_.*\.grib2$",
        r"^CMC_glb_WIND_ISBL_250_.*\.grib2$",   # if it exists in some deliveries
    ],
}


# -----------------------------
# CFG builder (REVISED)
# -----------------------------
def build_cfgs_for_fh(init_ymd: str, init_hh: str, fh: int, data_root="data_hpfx"):
    """
    Builds cfg dicts by DISCOVERING files within:
      data_root/YYYYMMDD/HH/FFF/*.grib2
    """
    data_root = Path(data_root)
    base_dir = data_root / init_ymd / init_hh / f"{fh:03d}"

    cfg500 = CFG_500.copy()
    cfg500["z500_grib"] = str(_find_one(base_dir, PAT["z500"]))
    cfg500["vort_grib"] = str(_find_one(base_dir, PAT["rv500"]))
    cfg500["valid_time_str"] = _valid_time_str(init_ymd, init_hh, fh)

    cfgmslp = CFG_MSLP.copy()
    cfgmslp["mslp_grib"] = str(_find_one(base_dir, PAT["mslp"]))
    cfgmslp["thk_grib"] = str(_find_one(base_dir, PAT["thk1000_500"]))

    cfg700 = CFG_700.copy()
    cfg700["z700_grib"] = str(_find_one(base_dir, PAT["z700"]))
    cfg700["rh500_grib"] = str(_find_one(base_dir, PAT["rh500"]))
    cfg700["rh700_grib"] = str(_find_one(base_dir, PAT["rh700"]))
    cfg700["rh850_grib"] = str(_find_one(base_dir, PAT["rh850"]))

    cfgpcpn = CFG_PCPN.copy()

    # Keep your existing logic: no precip at fh=0
    if fh == 0:
        cfgpcpn["show_precip"] = False
    else:
        cfgpcpn["show_precip"] = True
        cfgpcpn["pcpn_grib"] = str(_find_one(base_dir, PAT["pcpn"]))

    # Jet: only resolve if you actually enable it
    # (plot_precip has show_jet_core False by default)
    if cfgpcpn.get("show_jet_core", False):
        cfgpcpn["jet_spd_grib"] = str(_find_one(base_dir, PAT["wspd250"]))

    return cfg500, cfgmslp, cfg700, cfgpcpn


# -----------------------------
# Single-figure maker (UNCHANGED)
# -----------------------------
def make_4panel(
    cfg500,
    cfgmslp,
    cfg700,
    cfgpcpn,
    figsize=(11.8, 10),
    dpi=300,
    outname="GDPS_4panel.png",
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

   # t0 = time.perf_counter()
    plot_500hpa(cfg500, ax=ax500)
    add_panel_title(ax500, "500 hPa Height + Relative Vorticity (10⁻⁵ s⁻¹)", loc="bl")
  #  print(f"500mb: {time.perf_counter()-t0:.2f}s")

  #  t0 = time.perf_counter()
    plot_mslp_thickness(cfgmslp, ax=axmslp)
    add_panel_title(axmslp, "MSLP + 1000–500 Thickness", loc="bl")
  #  print(f"mslp: {time.perf_counter()-t0:.2f}s")

  #  t0 = time.perf_counter()
    plot_700hpa(cfg700, ax=ax700)
    add_panel_title(ax700, "700 hPa Height + 850-500 Relative Humidity", loc="bl")
   # print(f"700mb: {time.perf_counter()-t0:.2f}s")

  #  t0 = time.perf_counter()
    plot_pcpn12(cfgpcpn, ax=axpcpn)
    if cfgpcpn.get("show_precip", True):
        add_panel_title(axpcpn, "12H PCPN", loc="bl")
    else:
        add_panel_title(axpcpn, "No PCPN at 00H", loc="bl")
  #  print(f"pcpn: {time.perf_counter()-t0:.2f}s")

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
# Batch runner (UNCHANGED except uses new builder)
# -----------------------------
def batch_make_4panel_gdps(
    init_ymd: str,
    init_hh: str,
    fstart: int = 0,
    fend: int = 240,
    step: int = 12,
    data_dir: str = "data_hpfx",
    output_dir: str = "outputs",
    figsize=(11.8, 10),
    dpi: int = 300,
    skip_missing: bool = True,
):
    ROOT = get_project_root()
    data_dir_path = ROOT / data_dir
    print(data_dir_path)

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

        outname = f"GDPS_{init_ymd}T{init_hh}Z_F{fh:03d}_4panel.png"
        make_4panel(
            cfg500, cfgmslp, cfg700, cfgpcpn,
            figsize=figsize,
            dpi=dpi,
            outname=outname,
            output_dir=output_dir,
        )


if __name__ == "__main__":
    
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", default="", help='init time like 20260120T00Z (UTC)')
    ap.add_argument("--date", default="", help='UTC date YYYYMMDD (alternative to --init)')
    ap.add_argument("--cycle", default="", help='cycle HH (00 or 12) (alternative to --init)')
    ap.add_argument("--auto", action="store_true", help="auto-pick latest available init in data_dir")
    ap.add_argument("--lookback_days", type=int, default=2, help="for --auto, search back N days")
    ap.add_argument("--data_dir", default="data_hpfx")
    ap.add_argument("--out_base", default="outputs")  # base output folder
    ap.add_argument("--fstart", type=int, default=0)
    ap.add_argument("--fend", type=int, default=240)
    ap.add_argument("--step", type=int, default=12)
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
        # search newest existing folder: data_hpfx/YYYYMMDD/HH/
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
    output_dir = f"{args.out_base}/GEMGLO_{init_tag}"

    batch_make_4panel_gdps(
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
    # example
    # batch_make_4panel_gdps(
    #     init_ymd="20260213",
    #     init_hh="12",
    #     fstart=0,
    #     fend=12,
    #     step=12,
    #     data_dir="data_hpx",
    #     output_dir="outputs/GDPS_20260213T12Z",
    #     figsize=(11.8, 10),
    #     dpi=300,
    #     skip_missing=True,
    # )
