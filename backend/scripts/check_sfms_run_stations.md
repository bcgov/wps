# SFMS run stations vs. SFMS CSV extracts

Findings from comparing the SFMS CSV extracts for 2026-07-02 → 2026-07-12 against the
`sfms_run` rows in the wps database. Reproduce with:

```sh
cd backend
uv run python scripts/check_sfms_run_stations.py --dir ~/projects/data/sfms_stations_july_2_12
```

## What the two sides actually are

The comparison only makes sense once you know these are three different things:

| Source | What it contains |
| --- | --- |
| `stations_YYYYMMDD_HHMM.csv` | Spool of `APP_WF1_WEATHER.STATION_BC_ACTIVE_REPORTING_VW`: the **roster** of active reporting stations (264, near-constant over the window). |
| `weather_YYYYMMDD_HHMM.csv` | Spool of `APP_WF1_WEATHER.SFMS_DAILY_VW` for the current date: the stations SFMS **has weather data for** at dump time. |
| `sfms_run.stations` | Written in `app/jobs/sfms_daily_actuals.py` as the codes returned by `get_sfms_daily_actuals_all_stations`: the stations that **made it into the run**. |

The run is expected to be a subset of the roster. `is_sfms_daily`
(`packages/wps-wf1/src/wps_wf1/parsers.py`) applies the same station-pool criteria as the
Oracle view — valid station, `stationStatus == ACTIVE`, `siteType in SFMS_SITE_TYPE_IDS`
(the comment there says the site types were chosen to match the view) — and then adds one
condition the view has no concept of:

```python
and record_type_id in {record_type.value for record_type in record_types}  # ACTUAL, MANUAL
```

So a station enters a run only once WF1 has an ACTUAL or MANUAL daily for it.

## Reporting curve

Stations trickle in through the afternoon, which is why run size grows across the day's
three actual runs:

| Run | Stations in run (of 264) |
| --- | --- |
| 13:20 | 83–166 (≈31–63%) |
| 14:20 | 254–262 (≈96–99%) |
| 15:20 | 259–262 (≈98–99%) |

Every "roster station absent from the run" at 13:20 and 14:20 is explained by this.

## Findings

### 1. The 13:20 run is fed far less than SFMS had — unresolved

At 13:15 the weather extract has **181–200** stations with data, but the 13:20 run recorded
only **83–166**. The gap is **~50–114 stations, every day, all ten days**.

**Theory (unconfirmed):** those extra rows in `SFMS_DAILY_VW` are still FORECAST records.
The run only accepts ACTUAL/MANUAL, so skipping them would be correct and intentional. The
spool has no `record_type` column, so the CSVs cannot settle this.

**To resolve:** add `record_type` to the `SELECT` in `SFMS_weatherExtract.sql`, or query the
WF1 API for one of the missing codes at ~13:15 and check the daily's record type. This
matters — if the rows turn out to be ACTUALs, the first run of every day is systematically
under-fed by roughly a third of the network.

### 2. Three stations with data were missed by a final run — real misses

By the 15:20 run the gap closes to ~0, but not always:

| Station | Final runs it was left out of, despite having weather data |
| --- | --- |
| 213 | 2 of 10 |
| 170 | 1 of 10 |
| 1203 | 1 of 10 |

Record type does not excuse these — by the last run of the day an actual should exist.
Station **213** is the one to chase: it has a row in all 42 weather CSVs yet missed two
final runs.

### 3. Stations 1348 and 1349 never make it into any run — not our bug

Absent from all 10 final runs. They also have **no weather row in any of the 42 weather
CSVs**, so SFMS never had data for them. We are not dropping anything; these are roster
entries that never produce data. That is a station-registry question, not a pipeline one.

### 4. Station 1092 in a run but not the roster — roster lag, benign

Run 1860 (2026-07-10 15:20) included station 1092, which is absent from the 15:15 roster
dump. It first appears in the roster at the **16:15** dump the same day. The station went
active in WF1 between the dump and the run; the live API knew before the hourly spool did.
Only occurrence in the window.

### 5. The `_1615.csv` dumps match no run — expected

Twelve CSVs are unmatched because the last actual run of the day is 15:20, so nothing
follows a 16:15 dump within the matching window. Not a gap in the data.

## Notes

- `sfms_run.stations` is only ever compared here against runs of type `actual`; the CSV dump
  times never line up with the 08:00 / 17:45 forecast runs.
- Station codes appearing "in run, no data row" hold steady at ~4 per run. Not investigated;
  likely stations whose daily exists in WF1 but falls outside the `SFMS_DAILY_VW` timestamp
  predicate (`TRUNC(pst_weather_timestamp) = TRUNC(SYSDATE)`).
- The read role `wpsread` needed `GRANT SELECT ON sfms_run` in the local database before the
  script would run.
