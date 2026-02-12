# -*- coding: utf-8 -*-
"""
Generate a 2x2 4-panel plot for MANY forecast hours (6/12-hourly out to 10 days).

"""

import os
from pathlib import Path
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# -----------------------------
# Import GDPS plotters
# -----------------------------
from plot_500mb import plot_500hpa, CFG_500 as CFG_500
from plot_mslp import plot_mslp_thickness, CFG_MSLP as CFG_MSLP
from plot_700mb import plot_700hpa, CFG_700 as CFG_700
from plot_precip import plot_pcpn12, PLOT_CONFIG_PCPN12 as CFG_PCPN

from matplotlib.patches import Rectangle
import matplotlib.patheffects as PathEffects
import argparse
from datetime import datetime, timedelta
import time
import gc
import matplotlib
matplotlib.use("Agg")

# -----------------------------
# Import the panel settings
# -----------------------------
from panel_layout import (
    get_project_root,
    add_panel_title,
    add_valid_time_stamp,
    apply_4panel_frames,
)
# -----------------------------
# File naming + cfg builders
# -----------------------------
def gdps_fname(init_ymd: str, init_hh: str, field: str, level: str | None, fh: int,
              grid: str = "LatLon0.15") -> str:
    """
    If level is None/"" -> omit it from the filename.
    """
    level_part = f"_{level}" if level else ""
    return f"{init_ymd}T{init_hh}Z_MSC_GDPS_{field}{level_part}_{grid}_PT{fh:03d}H.grib2"



def _valid_time_str(init_ymd: str, init_hh: str, fh: int) -> str:
    """
    Build "F036 Valid: Tue 2025-12-30 00Z" (UTC)
    """
    init_dt = datetime.strptime(f"{init_ymd}{init_hh}", "%Y%m%d%H")
    valid_dt = init_dt + timedelta(hours=int(fh))
    return f"F{fh:03d} Valid: {valid_dt:%a %Y-%m-%d %HZ}"


def build_cfgs_for_fh(init_ymd: str, init_hh: str, fh: int,
                      data_root="data_hpfx"):
    """
    Build cfg dicts using HPFX directory structure:
    data_hpfx/YYYYMMDD/HH/FFF/*.grib2
    """
    data_root = Path(data_root)

    fh_dir = f"{fh:03d}"
    base_dir = data_root / init_ymd / init_hh / fh_dir

    cfg500 = CFG_500.copy()
    cfg500["z500_grib"] = str(
        base_dir / gdps_fname(init_ymd, init_hh, "GeopotentialHeight", "IsbL-0500", fh)
    )
    cfg500["vort_grib"] = str(
        base_dir / gdps_fname(init_ymd, init_hh, "RelativeVorticity", "IsbL-0500", fh)
    )
    cfg500["valid_time_str"] = _valid_time_str(init_ymd, init_hh, fh)

    cfgmslp = CFG_MSLP.copy()

    # ✅ Pressure_MSL has NO level token
    cfgmslp["mslp_grib"] = str(
        base_dir / gdps_fname(init_ymd, init_hh, "Pressure_MSL", None, fh)
    )
    
    cfgmslp["thk_grib"] = str(
        base_dir / gdps_fname(init_ymd, init_hh, "Thickness", "IsbL-1000to0500", fh)
    )

    

    cfg700 = CFG_700.copy()
    cfg700["z700_grib"] = str(
        base_dir / gdps_fname(init_ymd, init_hh, "GeopotentialHeight", "IsbL-0700", fh)
    )
    cfg700["rh500_grib"] = str(
        base_dir / gdps_fname(init_ymd, init_hh, "RelativeHumidity", "IsbL-0500", fh)
    )
    cfg700["rh700_grib"] = str(
        base_dir / gdps_fname(init_ymd, init_hh, "RelativeHumidity", "IsbL-0700", fh)
    )
    cfg700["rh850_grib"] = str(
        base_dir / gdps_fname(init_ymd, init_hh, "RelativeHumidity", "IsbL-0850", fh)
    )

    cfgpcpn = CFG_PCPN.copy()
    
    cfgpcpn["jet_spd_grib"] = str(
        base_dir / gdps_fname(init_ymd, init_hh, "WindSpeed", "IsbL-0250", fh)
    )
    if fh == 0:
       cfgpcpn["show_precip"] = False   # jet-only
    else:
       cfgpcpn["show_precip"] = True
       cfgpcpn["pcpn_grib"] = str(base_dir / gdps_fname(init_ymd, init_hh, "Precip-Accum12h", "Sfc", fh))

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
    
    t0 = time.perf_counter()
    plot_500hpa(cfg500, ax=ax500)
    add_panel_title(ax500, "500 hPa Height + Relative Vorticity (1×10⁻⁵ s⁻¹)", loc="bl")
    print(f"500mb: {time.perf_counter()-t0:.2f}s")

    t0 = time.perf_counter()
    plot_mslp_thickness(cfgmslp, ax=axmslp)
    add_panel_title(axmslp, "MSLP + 1000–500 Thickness", loc="bl")
    print(f"mslp: {time.perf_counter()-t0:.2f}s")

    t0 = time.perf_counter()
    plot_700hpa(cfg700, ax=ax700)
    add_panel_title(ax700, "700 hPa Height + 850-500 Relative Humidity", loc="bl") #RH (850/700/500)
    print(f"700mb: {time.perf_counter()-t0:.2f}s")

    
    t0 = time.perf_counter()
    plot_pcpn12(cfgpcpn, ax=axpcpn)
    if cfgpcpn.get("show_precip", True):
     #   add_panel_title(axpcpn, "12H PCPN + 250 hPa Jet", loc="bl")
        add_panel_title(axpcpn, "12H PCPN", loc="bl")
    else:
       # add_panel_title(axpcpn, "250 hPa Jet", loc="bl")
        add_panel_title(axpcpn, "No PCPN at 00H", loc="bl")
    print(f"pcpn: {time.perf_counter()-t0:.2f}s")
   
    apply_4panel_frames(fig, axes, add_outer_border=True)

    valid_text = cfg500.get("valid_time_str", "")
    if valid_text:
        add_valid_time_stamp(fig, valid_text, height=0.04, fontsize=14)

    outpath = outdir / outname
    fig.savefig(outpath, dpi=dpi, bbox_inches=None, pad_inches=0.0, facecolor="white")
    plt.close(fig)  # IMPORTANT for loops
    print("Saved:", outpath)
    return outpath

# -----------------------------
# Batch runner 
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
    """
    Makes 12-hourly maps for 10 days (0..240 by 12) for ONE GDPS run.
    """
    ROOT = get_project_root()
    data_dir_path = ROOT / data_dir
    print(data_dir_path)

    for fh in range(int(fstart), int(fend) + 1, int(step)):
        cfg500, cfgmslp, cfg700, cfgpcpn = build_cfgs_for_fh(init_ymd, init_hh, fh, data_root=data_dir_path)


        # check files exist
        needed = [
            cfg500["z500_grib"], cfg500["vort_grib"],
            cfgmslp["mslp_grib"], cfgmslp["thk_grib"],
            cfg700["z700_grib"], cfg700["rh500_grib"], cfg700["rh700_grib"], cfg700["rh850_grib"],
        ]
       
        # precip required only if show_precip
        if cfgpcpn.get("show_precip", True):
            needed.append(cfgpcpn["pcpn_grib"])
        
        # jet required if show_jet_core
        if cfgpcpn.get("show_jet_core", False):
            needed.append(cfgpcpn["jet_spd_grib"])

        missing = [p for p in needed if not Path(p).exists()]
        if missing:
            msg = f"[SKIP F{fh:03d}] missing {len(missing)} files, e.g. {missing[0]}"
            if skip_missing:
                print(msg)
                continue
            raise FileNotFoundError(msg)

        outname = f"GDPS_{init_ymd}T{init_hh}Z_F{fh:03d}_4panel.png"
        make_4panel(
            cfg500, cfgmslp, cfg700, cfgpcpn,
            figsize=figsize,
            dpi=dpi,
            outname=outname,
            output_dir=output_dir,
        )


if __name__ == "__main__":
    # Example: build 0..240 every 12h for the 2025-12-29 12Z GDPS run
    # ap = argparse.ArgumentParser()
    # ap.add_argument("--init", default="", help='init time like 20260120T00Z (UTC)')
    # ap.add_argument("--date", default="", help='UTC date YYYYMMDD (alternative to --init)')
    # ap.add_argument("--cycle", default="", help='cycle HH (00 or 12) (alternative to --init)')
    # ap.add_argument("--auto", action="store_true", help="auto-pick latest available init in data_dir")
    # ap.add_argument("--lookback_days", type=int, default=2, help="for --auto, search back N days")
    # ap.add_argument("--data_dir", default="data_hpfx")
    # ap.add_argument("--out_base", default="outputs")  # base output folder
    # ap.add_argument("--fstart", type=int, default=0)
    # ap.add_argument("--fend", type=int, default=240)
    # ap.add_argument("--step", type=int, default=12)
    # ap.add_argument("--dpi", type=int, default=300)
    # args = ap.parse_args()

    # ROOT = get_project_root()
    # data_root = ROOT / args.data_dir

    # def parse_init(s: str):
    #     # "20260120T00Z" -> ("20260120","00")
    #     s = s.strip().upper()
    #     if "T" in s:
    #         ymd, rest = s.split("T", 1)
    #         hh = rest.replace("Z", "")[:2]
    #         return ymd, hh
    #     raise ValueError("Bad --init format, expected YYYYMMDDTHHZ")

    # # ---- decide init_ymd / init_hh ----
    # if args.auto:
    #     # search newest existing folder: data_hpfx/YYYYMMDD/HH/
    #     candidates = []
    #     now = datetime.utcnow()
    #     for dd in range(args.lookback_days + 1):
    #         d = (now - timedelta(days=dd)).strftime("%Y%m%d")
    #         for hh in ["12", "00"]:  # prefer 12 then 00 if both exist on same day
    #             if (data_root / d / hh).exists():
    #                 # rank by datetime
    #                 dt = datetime.strptime(d + hh, "%Y%m%d%H")
    #                 candidates.append((dt, d, hh))
    #     if not candidates:
    #         raise FileNotFoundError(f"No init folders found under: {data_root}")
    #     candidates.sort()
    #     init_dt, init_ymd, init_hh = candidates[-1]
    # elif args.init.strip():
    #     init_ymd, init_hh = parse_init(args.init)
    # else:
    #     # use --date + --cycle
    #     if not args.date or not args.cycle:
    #         raise ValueError("Provide either --init, or (--date and --cycle), or use --auto.")
    #     init_ymd, init_hh = args.date.strip(), args.cycle.strip()

    # init_tag = f"{init_ymd}T{init_hh}Z"
    # output_dir = f"{args.out_base}/GDPS_{init_tag}"

    # batch_make_4panel_gdps(
    #     init_ymd=init_ymd,
    #     init_hh=init_hh,
    #     fstart=args.fstart,
    #     fend=args.fend,
    #     step=args.step,
    #     data_dir=args.data_dir,
    #     output_dir=output_dir,
    #     figsize=(11.8, 10),
    #     dpi=args.dpi,
    #     skip_missing=True,
    #)
      batch_make_4panel_gdps(
        init_ymd="20260130",
        init_hh="00",
        fstart=0,
        fend=240,
        step=12,
        data_dir="data_hpfx",
        output_dir="outputs/GDPS_20260130T00Z",  
        figsize=(11.8, 10),
        dpi=300,
        skip_missing=True,
    )