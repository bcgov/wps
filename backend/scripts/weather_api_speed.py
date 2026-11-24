"""Time the Station Weather API: typical requests one at a time, and several at once.

Each request is made a few times. The first is shown on its own, because it can be slower, and the
median and slowest are of the rest. Only reads.

From ./backend, through the gateway:

    WEATHER_API_KEY=... uv run python scripts/weather_api_speed.py

or straight to a pod, without the gateway or a key, with this running in another terminal:

    oc -n e1e498-dev port-forward deploy/wps-pr-123-weather 8088:8080
    uv run python scripts/weather_api_speed.py --url http://localhost:8088/api/weather/v1

The gateway allows 60 requests a minute, so requests are spaced out unless the URL is local.
"""

import argparse
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from urllib.parse import urlsplit

import requests

DEV = "https://psu-pr-6073-api-gov-bc-ca.test.api.gov.bc.ca/api/weather/v1"
GATEWAY_PAUSE_SECONDS = 1.1


def cases(station: int, stations: list[int]) -> dict[str, tuple[str, dict]]:
    """What to ask for, by a name for it: the path and the parameters."""
    today = date.today()
    many = ",".join(str(code) for code in stations[:20])
    daily, hourly = "/observations/daily", "/observations/hourly"
    return {
        "stations": ("/stations", {}),
        "1 station, last week, daily": (daily, {"station_codes": station}),
        "1 station, last 2 days, hourly": (
            hourly,
            {"station_codes": station, "start": today - timedelta(days=1), "end": today},
        ),
        "1 station, a past month, hourly": (
            hourly,
            {"station_codes": station, "start": "2025-07-01", "end": "2025-07-31"},
        ),
        "1 station, 36 years, daily": (
            daily,
            {"station_codes": station, "start": "1990-01-01", "end": "2025-12-31"},
        ),
        "20 stations, a year, daily": (
            daily,
            {"station_codes": many, "start": "2025-01-01", "end": "2025-12-31"},
        ),
        "1 station, HRDPS, hourly": ("/models/HRDPS/hourly", {"station_codes": station}),
    }


def timed(session: requests.Session, url: str, params: dict) -> tuple[float, float, int]:
    """Seconds to the first byte and to the last, and the bytes received."""
    started = time.perf_counter()
    with session.get(url, params=params, timeout=120, stream=True) as response:
        first_byte = time.perf_counter() - started
        size = len(response.content)
        finished = time.perf_counter() - started
        if not response.ok:
            raise SystemExit(f"{response.status_code} from {url}: {response.text[:300]}")
    return first_byte, finished, size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--url", default=os.environ.get("WEATHER_API_URL", DEV))
    parser.add_argument("--repeats", type=int, default=5, help="times to make each request")
    parser.add_argument("--station", type=int, default=322)
    parser.add_argument("--together", type=int, default=10, help="requests to make at once, or 0")
    args = parser.parse_args()
    if args.repeats < 2:
        parser.error("--repeats must be at least 2: the first is shown on its own")
    local = urlsplit(args.url).hostname in ("localhost", "127.0.0.1")
    pause = 0 if local else GATEWAY_PAUSE_SECONDS

    session = requests.Session()
    if os.environ.get("WEATHER_API_KEY"):
        session.headers["X-API-Key"] = os.environ["WEATHER_API_KEY"]
    print(f"{args.url}, {'with' if 'X-API-Key' in session.headers else 'without'} a key\n")

    response = session.get(args.url + "/stations", timeout=120)
    if not response.ok:
        raise SystemExit(f"{response.status_code} from {response.url}: {response.text[:300]}")
    codes = [station["station_code"] for station in response.json()["stations"]]
    time.sleep(pause)

    print(f"{'':34}{'first':>8}{'median':>8}{'slowest':>9}{'1st byte':>10}{'size':>11}")
    for name, (path, params) in cases(args.station, codes).items():
        runs = []
        for _ in range(args.repeats):
            runs.append(timed(session, args.url + path, params))
            time.sleep(pause)
        rest = runs[1:]
        print(
            f"{name:34}{runs[0][1]:7.2f}s{statistics.median(r[1] for r in rest):7.2f}s"
            f"{max(r[1] for r in rest):8.2f}s{statistics.median(r[0] for r in rest):9.2f}s"
            f"{rest[-1][2] / 1000:8,.0f} kB"
        )

    if args.together:
        # Leave the gateway's minute to empty first.
        time.sleep(pause * args.together)
        path, params = cases(args.station, codes)["1 station, last week, daily"]
        started = time.perf_counter()
        with ThreadPoolExecutor(args.together) as pool:
            runs = list(
                pool.map(lambda _: timed(session, args.url + path, params), range(args.together))
            )
        print(
            f"\n{args.together} at once (1 station, last week): all in "
            f"{time.perf_counter() - started:.2f}s, median {statistics.median(r[1] for r in runs):.2f}s, "
            f"slowest {max(r[1] for r in runs):.2f}s"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
