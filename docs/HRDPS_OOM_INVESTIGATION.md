# env-canada-hrdps OOMKilled investigation

## Incident

Two `PodOOMKilled` alerts fired around the same time:
- `env-canada-hrdps-wps-prod` (memory limit 1Gi) — this document.
- `wx-4panel-charts-rdps` (memory limit 4Gi) — **not investigated**; deprioritized once the HRDPS root-cause search took over. Worth a fresh pass; see "wx-4panel-charts-rdps" section below for what's already known about it.

**Confirmed pod**: `env-canada-hrdps-wps-prod-29743421-vsvlf`, namespace `e1e498-prod`.
**Timeline** (from Grafana `container_memory_working_set_bytes` + Loki logs, 2026-07-20):
- Pod started 21:06:12 PDT.
- Memory climbed from a ~350–400MB baseline to ~1.02G by 21:21:32 PDT — a **staircase**, not a smooth per-file climb or a single spike, spread over ~15 minutes across the pod's ~24-minute life.
- Last log line at 21:30:34 PDT was `apply_data_retention_policy()`'s `Deleting model_run_prediction data older than ...` — the very last step `run_model_job()` runs, *after* both the download/ingest phase and the interpolation phase complete. The climb to ~1G had already happened well before this line, so the delete itself is not the cause — it's just what was running when the pod finally died.
- Kubernetes restarted the container per `restartPolicy: OnFailure`; the new pod's baseline matched the original's starting point (~350–400MB), i.e. behavior is consistent and reproducible run-to-run, not some corrupted state.

The staircase shape (several distinct climb-then-plateau cycles, never resetting) pointed at something tied to a small, repeating boundary — HRDPS processes exactly 4 model-run hours (00/06/12/18Z) sequentially in one process — rather than a per-file leak (~245 files/hour) or a single large allocation.

## Hypotheses tested and ruled out

All of these were tested with real code paths (not mocks of the mechanism under test), and where noted, under conditions matching production as closely as could be reproduced locally.

| # | Hypothesis | Test | Result |
|---|---|---|---|
| 1 | GDAL/pyproj per-file decode loop leaks across ~245 sequential files | Real download + GDAL decode, 1 model-run hour, 244 real files | Plateaus (~410→446MB), no unbounded growth |
| 2 | SQLAlchemy write-session identity map grows unboundedly (single commit at job end, per `store_prediction_value`) | 245,000 real `store_prediction_value` calls against real Postgres, one un-flushed session | Completely flat |
| 3 | Per-station ML/interpolation (`StationMachineLearning`, sklearn) accumulates across stations before the per-run commit | 500 real stations, real sklearn fits, real DB session | Completely flat |
| 4 | Fresh `requests.Session()` per model-run hour (4/job, never closed) causes TLS/connection-pool fragmentation | 8 simulated hours × 30 real HTTPS requests to real ECCC servers, fresh session each time | Flat after one-time OpenSSL init cost |
| 5 | GDAL's global raster block cache defaults to host-RAM-sized (unaware of the container's cgroup limit), accumulating unboundedly across ~980 files/4 hours | Checked `gdal.GetCacheMax()` unconstrained (2.4GB on host) vs. under real podman `--memory` constraints | **Claim was wrong** — GDAL 3.13.1 reads the cgroup limit and computes 5% of it (12.8MB @ 256m, 51.2MB @ 1g). Not host-RAM-based. |
| 6 | Full real pipeline (`EnvCanada.process()`, all 4 hours, ~980 files) under the *actual* 1Gi cgroup constraint | Ran inside podman with `--memory=1g`, with the GDAL-cache fix both disabled and enabled | **Neither reproduced the OOM.** Both stayed in the ~440–550MB range across all 4 hours, exit code 0. |
| 7 | Interpolation phase, full `MAX_DAYS_TO_LEARN=19`-day history per station (vs. an earlier 72h test) | 300 stations × full 19-day seeded history, real sklearn | Flat |
| 8 | Interpolation phase, backlog of multiple pending model runs processed in one call (not just one) | 300 stations × 4 backlogged model runs, full 19-day history, real `_process_model_run` loop | Flat |

**Not yet tested**: the full three-phase sequence (`EnvCanada.process()` → `ModelValueProcessor.process()` → `apply_data_retention_policy()`) combined in one process, under the real 1Gi constraint. This is the one combination that matches production exactly and hasn't been tried — attempts were blocked by what looks like rate-limiting/throttling from ECCC's public servers (`hpfx.collab.science.gc.ca`) after this investigation's cumulative real-download volume (multiple full 4-hour runs). See `profile_full_pipeline.py` below — it's built and ready, just needs network conditions to recover (or a different network path/credentials).

## Changes made (uncommitted at time of writing)

1. **`weather_model_jobs/utils/process_grib.py`** — `gdal.SetCacheMax(128 * 1024 * 1024)` at module import. Explicit, deterministic bound on GDAL's global raster cache. **Not a confirmed fix** (see hypothesis 5/6 above) — kept as defensive hygiene since it removes reliance on GDAL's own auto-detection behaving consistently across versions/environments, and isn't harmful.
2. **`weather_model_jobs/env_canada.py`** — `EnvCanada` now takes an injected `requests.Session` (`http_session` constructor param) instead of creating its own per model-run-hour; `process_models()` creates one `requests.Session` and reuses it across all 4 hours, closed via context manager. Didn't independently reproduce growth in isolation (hypothesis 4), but is correct usage per `requests`' own guidance and removes a variable. Also makes `EnvCanada` easier to test (session lifecycle no longer hidden inside the constructor).
3. **`backend/packages/wps-weather/Dockerfile`** — added missing `python3-dev` to the builder stage's apt install. Unrelated to the OOM; needed to build the image locally on Apple Silicon (aarch64), where `fiona` has no prebuilt wheel and has to compile from source, which needs `Python.h`.

Test suite (`packages/wps-jobs/src/tests/weather_models/`, 193 tests) passes with all of the above.

## Profiling scripts left behind

All in `backend/packages/wps-jobs/src/weather_model_jobs/`, each with a usage docstring at the top:

- **`profile_hrdps_memory.py`** — real download+GDAL pipeline (`EnvCanada.process()`), all 4 hours, real DB session, synthetic WFWX stations (`--stations`). The main tool for testing phase 1 in isolation.
- **`profile_hrdps_session_growth.py`** — fast, isolated test of `store_prediction_value` / SQLAlchemy identity-map growth, no network or GDAL.
- **`profile_requests_session_growth.py`** — fast, isolated test of `requests.Session` churn (`--mode fresh|reuse|fresh-closed`) against real ECCC servers.
- **`profile_ml_interpolation_growth.py`** — interpolation phase in isolation, configurable station count and history window.
- **`profile_ml_backlog_growth.py`** — interpolation phase with a simulated multi-run backlog and the full 19-day history window. No network calls.
- **`profile_full_pipeline.py`** — **the one still worth running to completion.** All three phases (`EnvCanada.process()` → `ModelValueProcessor.process()` → `apply_data_retention_policy()`) in one process, matching `run_model_job()` exactly. Needs `DATA_RETENTION_THRESHOLD` set in the environment (not needed by the other scripts). Intended to run inside podman with `--memory=1g`:
  ```bash
  podman run --rm --memory=1g \
      -v "$(pwd)/backend/packages/wps-jobs/src/weather_model_jobs":/app/weather_model_jobs \
      -e POSTGRES_WRITE_HOST=host.containers.internal \
      -e POSTGRES_READ_HOST=host.containers.internal \
      -e DATA_RETENTION_THRESHOLD=30 \
      wps-jobs:local \
      uv run --package wps-jobs --no-sync python -m weather_model_jobs.profile_full_pipeline --stations 500
  ```

Also relevant for anyone re-running these: local Postgres needs the `wps-api` alembic migrations applied (`uv run alembic upgrade head` from `backend/packages/wps-api`) — a pre-existing native Postgres on this machine already had them applied, no new setup was required here.

## `wx-4panel-charts-rdps` — not investigated

Original hypothesis (untested): the tricontour/Delaunay triangulation plotting pipeline (`plot_700mb_rdps.py` etc., merged 2026-03-31, +3118 lines, never load-tested) is genuinely memory-heavy per panel — 4Gi may just be an untuned initial guess. Also uses GDAL-adjacent libraries (cartopy); worth checking whether `gdal.SetCacheMax` is relevant there too, though the mechanism would likely be different (matplotlib/cartopy rendering, not raster block caching).

## Recommended next steps

1. Retry `profile_full_pipeline.py` under `--memory=1g` once ECCC's servers stop rate-limiting this environment (or run it from a different network path).
2. If it reproduces the OOM, bisect which of the three phases (or their combination) is responsible using the isolated scripts above as reference points.
3. If it *doesn't* reproduce even combined, consider that the real incident may need real WFWX credentials (real station count/roster, vs. this investigation's synthetic stand-ins) or may require pulling the actual `e1e498-prod` pod's metrics again to see if a *second* occurrence shows the same staircase shape (confirms it's systemic, not a one-off) before continuing to chase it locally.
4. Give `wx-4panel-charts-rdps` its own pass — it was set aside, not ruled out.
