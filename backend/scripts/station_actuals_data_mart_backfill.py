"""Copy historical station observations from the BCWS data mart into object storage.

The data mart publishes every station's hourly observations back to 1987:
https://www.for.gov.bc.ca/ftp/HPR/external/!publish/BCWS_DATA_MART/. This downloads them a year
at a time and writes them as `ACTUALS` to `wf1` and `by_time`, hourly and daily, so that
climatology has history from before the hourly actuals job wrote to these tables. The daily rows
are the noon rows that carry WF1's daily precip total.

Run from ./backend against the deployment's bucket:

    uv run python scripts/station_actuals_data_mart_backfill.py --from-year 1987
    uv run python scripts/station_actuals_data_mart_backfill.py --from-year 2026 --to-year 2026

A year is read from its whole-year file where there is one, and from its daily files otherwise,
as for the current year.

The script can be run again: `wf1` only takes a row that differs from the version before it,
and `by_time` keeps a value the hourly actuals job fetched from WF1 over one from here.
Exits 0 when every year was copied, 1 otherwise.

Design: docs/architecture/station-weather-storage.md
"""

import argparse
import http.client
import logging
import re
import sys
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pyarrow as pa
from wps_shared.utils.time import get_utc_now
from wps_weather_data.by_time import BY_TIME_SCHEMA, ByTimeTable
from wps_weather_data.data_mart import read_observations_file, write_observations
from wps_weather_data.wf1 import Wf1Table

DATA_MART_URL = "https://www.for.gov.bc.ca/ftp/HPR/external/!publish/BCWS_DATA_MART"
FIRST_YEAR = 1987
# The server sends under 1 MB a second on one connection, and a whole-year file is over 200 MB,
# so a file is downloaded in parts over several connections at once.
CONNECTIONS = 8
PART_BYTES = 8_000_000
TIMEOUT_SECONDS = 120
ATTEMPTS = 3
# How often to report progress through a year's daily files.
PROGRESS_EVERY_FILES = 25

_CSV_LINK = re.compile(r'href="[^"]*/([^"/]+\.csv)"', re.IGNORECASE)
_DAILY_FILE = re.compile(r"^\d{4}-\d{2}-\d{2}\.csv$")


def report(message: str):
    """Print progress straight away, also when the output is piped."""
    print(message, flush=True)


def request(url: str, *, method: str = "GET", byte_range: tuple[int, int] | None = None):
    """Open a URL, retrying a failure. Returns the response's headers and body."""
    headers = {"Range": f"bytes={byte_range[0]}-{byte_range[1]}"} if byte_range else {}
    for attempt in range(1, ATTEMPTS + 1):
        try:
            http_request = urllib.request.Request(url, method=method, headers=headers)
            with urllib.request.urlopen(http_request, timeout=TIMEOUT_SECONDS) as response:
                body = response.read()
                if byte_range and len(body) != byte_range[1] - byte_range[0] + 1:
                    raise OSError(f"got {len(body)} bytes for range {byte_range}")
                return response.headers, body
        # A connection that drops part way through is an HTTPException, not an OSError.
        except (OSError, http.client.HTTPException) as error:
            if attempt == ATTEMPTS:
                raise
            report(f"[retrying   ] {url}: {type(error).__name__}")
            time.sleep(5 * attempt)
    raise AssertionError("unreachable")


def download_whole(url: str, path: Path):
    """Download a file on one connection."""
    path.write_bytes(request(url)[1])


def download(url: str, path: Path, pool: ThreadPoolExecutor, label: str):
    """Download a file, in parts over several connections if it is large, reporting progress as
    the parts arrive."""
    headers, _ = request(url, method="HEAD")
    size = int(headers.get("Content-Length") or 0)
    if size <= PART_BYTES or headers.get("Accept-Ranges") != "bytes":
        download_whole(url, path)
        return
    ranges = [(start, min(start + PART_BYTES, size) - 1) for start in range(0, size, PART_BYTES)]
    parts = {pool.submit(request, url, byte_range=byte_range): byte_range for byte_range in ranges}
    done = 0
    reported = 0
    with open(path, "wb") as file:
        file.truncate(size)
        for part in as_completed(parts):
            file.seek(parts[part][0])
            file.write(part.result()[1])
            done += 1
            percent = 100 * done // len(ranges)
            if percent >= reported + 10:
                reported = percent
                report(f"[downloading] {label}: {percent}% of {size / 1e6:.0f} MB")


def observation_files(year: int) -> list[str]:
    """The names of the files that hold a year's observations."""
    listing = request(f"{DATA_MART_URL}/{year}/")[1].decode()
    names = set(_CSV_LINK.findall(listing))
    whole_year = f"{year}_BCWS_WX_OBS.csv"
    if whole_year in names:
        return [whole_year]
    return sorted(name for name in names if _DAILY_FILE.match(name))


def read_year(year: int, names: list[str], directory: Path) -> pa.Table:
    """Download a year's files and read them as `ACTUALS` rows, reporting progress."""
    started = time.perf_counter()
    paths = [directory / name for name in names]
    with ThreadPoolExecutor(CONNECTIONS) as pool:
        if len(names) == 1:
            report(f"[downloading] {year}: {names[0]}")
            download(f"{DATA_MART_URL}/{year}/{names[0]}", paths[0], pool, label=str(year))
        else:
            # The daily files are small: several at once, each on one connection.
            downloads = [
                pool.submit(download_whole, f"{DATA_MART_URL}/{year}/{name}", path)
                for name, path in zip(names, paths)
            ]
            for count, finished in enumerate(as_completed(downloads), start=1):
                finished.result()
                if count % PROGRESS_EVERY_FILES == 0 or count == len(names):
                    report(f"[downloading] {year}: {count} of {len(names)} files")
    megabytes = sum(path.stat().st_size for path in paths) / 1e6
    report(f"[downloaded ] {year}: {megabytes:.0f} MB in {time.perf_counter() - started:.0f} s")

    started = time.perf_counter()
    batches = []
    for path in paths:
        batches.extend(read_observations_file(str(path)))
        path.unlink()
    rows = pa.concat_tables(batches) if batches else BY_TIME_SCHEMA.empty_table()
    report(f"[read       ] {year}: {rows.num_rows} rows in {time.perf_counter() - started:.0f} s")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--from-year", type=int, default=FIRST_YEAR)
    parser.add_argument("--to-year", type=int, default=get_utc_now().year)
    parser.add_argument(
        "--dry-run", action="store_true", help="download and read the files, but write nothing"
    )
    args = parser.parse_args()

    # The package logs each month as it is written.
    logging.basicConfig(level=logging.WARNING, format="[%(levelname)-11s] %(message)s")
    logging.getLogger("wps_weather_data.data_mart").setLevel(logging.INFO)

    wf1 = Wf1Table()
    by_time = ByTimeTable()
    report(f"Years {args.from_year} to {args.to_year}, writing to {by_time.table_uri}")
    failed = 0
    with tempfile.TemporaryDirectory() as directory:
        for year in range(args.from_year, args.to_year + 1):
            try:
                names = observation_files(year)
                rows = read_year(year, names, Path(directory))
                if args.dry_run:
                    report(f"[would copy ] {year}: {rows.num_rows} rows in {len(names)} files")
                    continue
                started = time.perf_counter()
                written = write_observations(wf1, by_time, rows)
                report(
                    f"[copied     ] {year}: {written['read']} rows in {len(names)} files, "
                    f"{written['daily']} of them daily, "
                    f"{written['wf1']} to wf1, {written['by_time']} to by_time "
                    f"in {time.perf_counter() - started:.0f} s"
                )
            except Exception as exception:
                failed += 1
                report(f"[failed     ] {year}: {exception}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
