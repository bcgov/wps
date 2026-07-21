"""
Fast, isolated test of whether creating a NEW requests.Session per model-run
hour (current ECCCUrlFetcher behaviour -- a fresh Session for every hour,
never explicitly closed) causes RSS to ratchet upward across hours, versus
reusing one Session, or explicitly closing each one when done.

This targets the mechanism suggested by the production memory graph: RSS
climbs in discrete steps that never come back down, at a cadence that lines
up with model-run-hour boundaries (env_canada.py's process_model_run creates
a fresh ECCCUrlFetcher -> fresh requests.Session for every one of HRDPS's 4
hours). The likely cause isn't a Python-level reference leak (the Session,
its PoolManager, and pooled connections are correctly dereferenced once the
fetcher goes out of scope -- no cycles requiring the GC) but glibc malloc
arena fragmentation from repeated TLS connection setup/teardown across many
HTTPS requests per session: memory that Python's refcounting correctly frees
at the object level often isn't returned to the OS by the C allocator, so
RSS as measured by the container's working set can ratchet upward across
churn cycles even though nothing is "leaked" in the traditional sense.

Usage (run each mode and compare the final peak RSS):
    uv run --package wps-jobs python -m weather_model_jobs.profile_requests_session_growth --mode fresh
    uv run --package wps-jobs python -m weather_model_jobs.profile_requests_session_growth --mode reuse
    uv run --package wps-jobs python -m weather_model_jobs.profile_requests_session_growth --mode fresh-closed
"""

import argparse
import sys
from datetime import datetime, timezone

import requests
import resource

from wps_shared.weather_models.model_run_urls import get_high_res_model_run_download_urls


def _rss_mb() -> float:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is bytes on macOS, KB on Linux.
    return peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024


def _fetch_batch(session: requests.Session, urls: list, timeout: int = 60) -> int:
    ok = 0
    for url in urls:
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code == 200:
                ok += 1
        except requests.RequestException:
            pass
    return ok


def main():
    parser = argparse.ArgumentParser(description="Test requests.Session churn vs. RSS growth against real ECCC servers.")
    parser.add_argument("--mode", choices=["fresh", "reuse", "fresh-closed"], default="fresh")
    parser.add_argument("--sessions", type=int, default=8, help="Number of simulated model-run hours.")
    parser.add_argument("--requests-per-session", type=int, default=30)
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    all_urls = list(get_high_res_model_run_download_urls(now, 0))
    urls = all_urls[: args.requests_per_session]
    print(f"{len(urls)} real HRDPS urls per simulated session, {args.sessions} sessions, mode={args.mode}")
    print(f"peak RSS before loop: {_rss_mb():.1f} MB")

    reused_session = requests.Session() if args.mode == "reuse" else None

    for i in range(args.sessions):
        session = reused_session if args.mode == "reuse" else requests.Session()

        ok = _fetch_batch(session, urls)

        if args.mode == "fresh-closed":
            session.close()
        # mode == "fresh": intentionally never closed -- matches current ECCCUrlFetcher behaviour.
        # mode == "reuse": same session object kept alive across every iteration.

        print(f"[session {i + 1:>2}/{args.sessions}] {ok}/{len(urls)} ok, peak RSS so far: {_rss_mb():.1f} MB")


if __name__ == "__main__":
    main()
