# -*- coding: utf-8 -*-
"""
Download GDPS 15km GRIB2 files from hpfx for our 4-panel workflow.

Structure:
  https://hpfx.collab.science.gc.ca/YYYYMMDD/WXO-DD/model_gdps/15km/{cycle}/{fhr:03d}/

Example file naming:
  20251229T12Z_MSC_GDPS_..._PT012H.grib2

- Downloads only files matching `PATTERNS`.
- Loops over dates, cycles (00/12), and forecast hours (0..240 step 12).
- Skips existing files.
"""

from __future__ import annotations

import re
import sys
import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Dict
import os
import requests


BASE = "https://hpfx.collab.science.gc.ca"


# ---- customize what you download (substring match) ----
# These substrings exist in the directory listing filenames (see hpfx index).
PATTERNS_DEFAULT = [
    # 500 hPa panel
    "_GeopotentialHeight_IsbL-0500_",
    "_RelativeVorticity_IsbL-0500_",

    # MSLP + thickness panel
    "_Pressure_MSL_",
    "_Thickness_IsbL-1000to0500_",

    # 700 hPa panel (adjust if your script uses different vars)
    "_GeopotentialHeight_IsbL-0700_",
    "_RelativeHumidity_IsbL-0700_",
    "_RelativeHumidity_IsbL-0850_",
    "_RelativeHumidity_IsbL-0500_",

    # precip + jet
    "_Precip-Accum12h_Sfc_",
    "_WindSpeed_IsbL-0250_",
]


@dataclass
class DownloadSpec:
    date_yyyymmdd: str
    cycle: str              # "00" or "12"
    fhr: int                # 0, 12, 24, ...
    outdir: Path


def daterange(start_yyyymmdd: str, ndays: int) -> List[str]:
    d0 = datetime.strptime(start_yyyymmdd, "%Y%m%d").date()
    return [(d0 + timedelta(days=i)).strftime("%Y%m%d") for i in range(ndays)]
        

def list_dir(url: str, timeout: int = 30) -> List[str]:
    """
    Parse Apache-like 'Index of' HTML, return file names (not directories).
    """
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()

    # Grab href="filename"
    hrefs = re.findall(r'href="([^"]+)"', r.text)
    names = []
    for h in hrefs:
        # ignore parent dir and subdirs
        if h in ("../",) or h.endswith("/"):
            continue
        names.append(h)
    return names


def download_file(url: str, dest: Path, timeout: int = 60) -> None:
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
    folder_url = f"{BASE}/{spec.date_yyyymmdd}/WXO-DD/model_gdps/15km/{spec.cycle}/{spec.fhr:03d}/"
    print(f"\nListing: {folder_url}")

    try:
        names = list_dir(folder_url)
    except Exception as e:
        print(f"  ERROR listing folder: {e}")
        return 0

    # filter
    wanted = []
    for n in names:
        if not n.endswith(".grib2"):
            continue
        if any(p in n for p in patterns):
            wanted.append(n)

    if not wanted:
        print("  (no matches)")
        return 0

    # download
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
    ap.add_argument("--start", required=True, help="start date YYYYMMDD (e.g. 20251229)")
    ap.add_argument("--days", type=int, default=1, help="number of days to download")
    ap.add_argument("--cycles", default="00,12", help='comma list, e.g. "00,12"')
    ap.add_argument("--step", type=int, default=12, help="forecast hour step (default 12)")
    ap.add_argument("--maxhr", type=int, default=240, help="max forecast hour (default 240 for 10 days)")
    ap.add_argument("--out", default="data_hpfx", help="output folder")
    ap.add_argument("--patterns", default="", help="optional: comma-separated substrings to match")
    args = ap.parse_args()

    cycles = [c.strip() for c in args.cycles.split(",") if c.strip()]
    outdir = Path(args.out).resolve()

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
