# -*- coding: utf-8 -*-
"""
Download RDPS GRIB2 files from hpfx for our 4-panel workflow.

https://hpfx.collab.science.gc.ca/YYYYMMDD/WXO-DD/model_rdps/10km/{cycle}/{fhr:03d}/

Example file naming:
  20260106T06Z_MSC_RDPS_GeopotentialHeight_IsbL-0500_RLatLon0.09_PT003H.grib2

- Downloads only files matching `PATTERNS`.
- Loops over dates, cycles, and forecast hours (0..84 step 3).
- Skips existing files.
"""

from __future__ import annotations

import re
import sys
import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import requests


BASE = "https://hpfx.collab.science.gc.ca"

# ---- RDPS path ----
MODEL_PATH = "WXO-DD/model_rdps/10km"   # <-- change if your hpfx uses another folder name

# These substrings exist in the directory listing filenames (see hpfx index).
PATTERNS_DEFAULT = [
    # 500 hPa panel
    "_GeopotentialHeight_IsbL-0500_",
    "_AbsoluteVorticity_IsbL-0500_",

    # MSLP + thickness (RDPS often has MSL pressure file similar naming)
    "_Pressure_MSL_",
    "_Thickness_IsbL-1000to0500_",

    # 700 hPa panel
    "_GeopotentialHeight_IsbL-0700_",
    "_RelativeHumidity_IsbL-0700_",
    "_RelativeHumidity_IsbL-0850_",
    "_RelativeHumidity_IsbL-0500_",

    # precip + jet
    "_Precip-Accum3h",
    "_WindSpeed_IsbL-0250_",
]


@dataclass
class DownloadSpec:
    date_yyyymmdd: str
    cycle: str              # e.g. "00", "06", "12", "18" (RDPS often 6-hourly cycles)
    fhr: int                # 0, 3, 6, ...
    outdir: Path


def get_project_root() -> Path:
    """
    Assumes script is under .../src/ and project root is one level up.
    """
    if "__file__" in globals():
        return Path(__file__).resolve().parents[1]
    # fallback: when run from an IDE console with cwd=.../src
    return Path.cwd().resolve().parents[1]


def daterange(start_yyyymmdd: str, ndays: int) -> List[str]:
    d0 = datetime.strptime(start_yyyymmdd, "%Y%m%d").date()
    return [(d0 + timedelta(days=i)).strftime("%Y%m%d") for i in range(ndays)]


def list_dir(url: str, timeout: int = 30) -> List[str]:
    """
    Parse Apache-like 'Index of' HTML, return file names (not directories).
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


def run_one_folder(spec: DownloadSpec, patterns: List[str]) -> int:
    folder_url = f"{BASE}/{spec.date_yyyymmdd}/{MODEL_PATH}/{spec.cycle}/{spec.fhr:03d}/"
    print(f"\nListing: {folder_url}")

    try:
        names = list_dir(folder_url)
    except Exception as e:
        print(f"  ERROR listing folder: {e}")
        return 0

    wanted = []
    for n in names:
        if not n.endswith(".grib2"):
            continue
        if any(p in n for p in patterns):
            wanted.append(n)

    if not wanted:
        print("  (no matches)")
        return 0

    count = 0
    for n in wanted:
        file_url = folder_url + n
        dest = spec.outdir / spec.date_yyyymmdd / spec.cycle / f"{spec.fhr:03d}" / n
        try:
            download_file(file_url, dest)
            count += 1
        except Exception as e:
            print(f"  ERROR downloading {n}: {e}")

    return count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="start date YYYYMMDD (e.g. 20260106)")
    ap.add_argument("--days", type=int, default=1, help="number of days to download")

    # RDPS often runs 00/06/12/18. Keep flexible:
    ap.add_argument("--cycles", default="00,06,12,18", help='comma list, e.g. "00,06,12,18"')

    ap.add_argument("--step", type=int, default=3, help="forecast hour step (default 3)")
    ap.add_argument("--maxhr", type=int, default=84, help="max forecast hour (default 84)")

    ap.add_argument("--out", default="data_hpfx", help="output folder (under project root)")
    ap.add_argument("--patterns", default="", help="optional: comma-separated substrings to match")
    args = ap.parse_args()

    cycles = [c.strip() for c in args.cycles.split(",") if c.strip()]

    ROOT = get_project_root()
    outdir = (ROOT / args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading into: {outdir}")

    patterns = PATTERNS_DEFAULT
    if args.patterns.strip():
        patterns = [p.strip() for p in args.patterns.split(",") if p.strip()]

    dates = daterange(args.start, args.days)
    fhrs = list(range(0, args.maxhr + 1, args.step))

    total = 0
    for d in dates:
        for cyc in cycles:
            for fhr in fhrs:
                spec = DownloadSpec(
                    date_yyyymmdd=d,
                    cycle=cyc,
                    fhr=fhr,
                    outdir=outdir,
                )
                total += run_one_folder(spec, patterns)

    print(f"\nDone. Downloaded {total} files into: {outdir}")


if __name__ == "__main__":
    sys.exit(main())
