# -*- coding: utf-8 -*-
"""
Download operational GEM global (GDPS 15km) GRIB2 files from hpfx/dd for our 4-panel workflow.

Folder structure (operational GEM global):
  https://hpfx.collab.science.gc.ca/YYYYMMDD/WXO-DD/model_gem_global/15km/grib2/lat_lon/{cycle}/{fhr:03d}/

Filename style:
  CMC_glb_<VAR>_<LEVEL>_latlon.15x.15_YYYYMMDDCC_PFFF.grib2

- Downloads only files matching PATTERNS (regex).
- Loops over dates, cycles, and forecast hours.
- Skips existing files.
"""

from __future__ import annotations

import re
import sys
import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Iterable, Dict
import requests

BASE = "https://hpfx.collab.science.gc.ca"
SUBPATH = "WXO-DD/model_gem_global/15km/grib2/lat_lon"

# ---- regex patterns for what you need ----
# Adjust/extend as your 4-panel evolves.
PATTERNS_DEFAULT = [
    # 500 hPa panel
    r"_HGT_ISBL_500_",
    r"_RELV_ISBL_500_",      # Relative vorticity (GEM naming)
    # If your vorticity uses a different token later, we can tweak this.

    # MSLP + thickness panel
    r"_PRMSL_MSL_0_",         # mean sea level pressure
    r"_HGT_ISBY_1000-500_",   # operational “thickness-like” field (1000–500) (seen on dd)
    # If you ever need to compute thickness instead, add:
    # r"_HGT_ISBL_1000_", r"_HGT_ISBL_500_",

    # 700 hPa panel
    r"_HGT_ISBL_700_",
    r"_RH_ISBL_700_",
    r"_RH_ISBL_850_",
    r"_RH_ISBL_500_",

    # precip + jet
    r"_APCP-Accum12h_SFC_0_",          # precip accumulation (naming varies by hour; this catches common one)
    r"_UGRD_ISBL_250_",                # jet u-component
    r"_VGRD_ISBL_250_",                # jet v-component
]

@dataclass
class DownloadSpec:
    date_yyyymmdd: str
    cycle: str
    fhr: int
    outdir: Path


def daterange(start_yyyymmdd: str, ndays: int) -> List[str]:
    d0 = datetime.strptime(start_yyyymmdd, "%Y%m%d").date()
    return [(d0 + timedelta(days=i)).strftime("%Y%m%d") for i in range(ndays)]


def list_dir(url: str, timeout: int = 30) -> List[str]:
    """
    Parse Apache-like index HTML, return file names (not directories).
    """
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()

    hrefs = re.findall(r'href="([^"]+)"', r.text)
    names = []
    for h in hrefs:
        if h in ("../",) or h.endswith("/"):
            continue
        names.append(h)
    return names


def download_file(url: str, dest: Path, timeout: int = 120) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  skip (exists): {dest.name}")
        return

    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        tmp.replace(dest)
    print(f"  saved: {dest.name}")


def folder_url_for(spec: DownloadSpec) -> str:
    return f"{BASE}/{spec.date_yyyymmdd}/{SUBPATH}/{spec.cycle}/{spec.fhr:03d}/"


def compile_patterns(patterns: List[str]) -> List[re.Pattern]:
    return [re.compile(p) for p in patterns]


def show_available_vars(names: List[str]) -> Dict[str, int]:
    """
    Quick “inventory”: count occurrences of the VAR token in CMC_glb_<VAR>_...
    """
    counts: Dict[str, int] = {}
    for n in names:
        if not n.endswith(".grib2"):
            continue
        m = re.match(r"CMC_glb_([^_]+)_", n)
        if not m:
            continue
        var = m.group(1)
        counts[var] = counts.get(var, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def run_one_folder(spec: DownloadSpec, patterns_re: List[re.Pattern], show_vars: bool = False) -> int:
    url = folder_url_for(spec)
    print(f"\nListing: {url}")

    try:
        names = list_dir(url)
    except Exception as e:
        print(f"  ERROR listing folder: {e}")
        return 0

    if show_vars:
        inv = show_available_vars(names)
        print("  Variables found (top):")
        for k, v in list(inv.items())[:30]:
            print(f"    {k}: {v}")
        # keep going; still allow downloads if patterns match

    wanted = []
    for n in names:
        if not n.endswith(".grib2"):
            continue
        if any(p.search(n) for p in patterns_re):
            wanted.append(n)

    if not wanted:
        print("  (no matches)")
        return 0

    count = 0
    for n in wanted:
        file_url = url + n
        dest = spec.outdir / spec.date_yyyymmdd / spec.cycle / f"{spec.fhr:03d}" / n
        try:
            download_file(file_url, dest)
            count += 1
        except Exception as e:
            print(f"  ERROR downloading {n}: {e}")

    return count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="start date YYYYMMDD (e.g. 20260213)")
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--cycles", default="00,12")
    ap.add_argument("--step", type=int, default=12)
    ap.add_argument("--maxhr", type=int, default=240)
    ap.add_argument("--out", default="data_hpfx")
    ap.add_argument("--patterns", default="", help="optional: comma-separated regex patterns")
    ap.add_argument("--show-vars", action="store_true", help="print a variable inventory per folder")
    args = ap.parse_args()

    cycles = [c.strip() for c in args.cycles.split(",") if c.strip()]
    outdir = Path(args.out).resolve()

    patterns = PATTERNS_DEFAULT
    if args.patterns.strip():
        patterns = [p.strip() for p in args.patterns.split(",") if p.strip()]
    patterns_re = compile_patterns(patterns)

    dates = daterange(args.start, args.days)
    fhrs = list(range(0, args.maxhr + 1, args.step))

    total = 0
    for d in dates:
        for cyc in cycles:
            for fhr in fhrs:
                spec = DownloadSpec(d, cyc, fhr, outdir)
                total += run_one_folder(spec, patterns_re, show_vars=args.show_vars)

    print(f"\nDone. Downloaded {total} files into: {outdir}")


if __name__ == "__main__":
    sys.exit(main())
