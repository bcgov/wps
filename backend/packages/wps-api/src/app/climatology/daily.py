"""Daily climatology: how a variable has been distributed on each day of the year.

The values are daily actuals, which are WF1's noon (20:00 UTC) records, less any WF1 marked
invalid. One year is held out
to compare against the others, so a year in progress does not shift the distribution it is
being compared with. Several stations can be combined, as a ClimatologyMethod describes, or
summarized one by one.
"""

from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from statistics import fmean

import numpy as np
import pyarrow as pa
from wps_shared.schemas.climatology import (
    ClimatologyDay,
    ClimatologyMethod,
    ClimatologyObservation,
    ClimatologySeries,
    ClimatologyVariable,
    DailyClimatologyResponse,
)

# A leap day has a value in one year of four, too few to describe, so it is left out.
_LEAP_DAY = (2, 29)
_PERCENTILES = (0, 25, 50, 75, 90, 100)

# date -> station code -> value
_ValuesByDate = dict[date, dict[int, float]]


def _values_by_station(rows: pa.Table, variable: ClimatologyVariable) -> dict[int, _ValuesByDate]:
    """Each station's values by date, from rows as `ByStationTable.read_stations` returns them."""
    by_station: dict[int, _ValuesByDate] = defaultdict(lambda: defaultdict(dict))
    for station_code, timestamp, value, valid in zip(
        rows["station_code"].to_pylist(),
        rows["timestamp"].to_pylist(),
        rows[variable.value].to_pylist(),
        rows["observation_valid"].to_pylist(),
        strict=True,
    ):
        # A record WF1 rejected is left out. A data mart observation does not say, so it is kept.
        if value is not None and valid is not False:
            # The daily record is at 20:00 UTC, noon PST, so the UTC date is the local date.
            by_station[station_code][timestamp.date()][station_code] = value
    return by_station


def _merge(values: Sequence[_ValuesByDate]) -> _ValuesByDate:
    merged: _ValuesByDate = defaultdict(dict)
    for by_date in values:
        for day, by_station in by_date.items():
            merged[day].update(by_station)
    return merged


def _series(
    by_date: _ValuesByDate, station_codes: list[int], year: int, pooled: bool
) -> ClimatologySeries:
    """Summarize values by date into a climatology, holding out `year`."""
    values_by_day: dict[tuple[int, int], list[float]] = defaultdict(list)
    stations_by_day: dict[tuple[int, int], set[int]] = defaultdict(set)
    observations: list[ClimatologyObservation] = []
    reference_years: set[int] = set()
    for day, by_station in by_date.items():
        if not by_station:
            continue
        if day.year == year:
            observations.append(
                ClimatologyObservation(
                    date=day, value=fmean(by_station.values()), station_count=len(by_station)
                )
            )
            continue
        key = (day.month, day.day)
        if key == _LEAP_DAY:
            continue
        if pooled:
            values_by_day[key].extend(by_station.values())
        else:
            values_by_day[key].append(fmean(by_station.values()))
        stations_by_day[key].update(by_station)
        reference_years.add(day.year)

    days = []
    for (month, day), values in sorted(values_by_day.items()):
        minimum, p25, median, p75, p90, maximum = (
            float(value) for value in np.percentile(values, _PERCENTILES)
        )
        days.append(
            ClimatologyDay(
                month=month,
                day=day,
                count=len(values),
                station_count=len(stations_by_day[(month, day)]),
                minimum=minimum,
                p25=p25,
                median=median,
                p75=p75,
                p90=p90,
                maximum=maximum,
            )
        )
    return ClimatologySeries(
        station_codes=station_codes,
        first_reference_year=min(reference_years, default=None),
        last_reference_year=max(reference_years, default=None),
        days=days,
        observations=sorted(observations, key=lambda observation: observation.date),
    )


def daily_climatology(
    rows: pa.Table,
    station_codes: Sequence[int],
    variable: ClimatologyVariable,
    year: int,
    method: ClimatologyMethod = ClimatologyMethod.AVERAGE,
) -> DailyClimatologyResponse:
    """Summarize the stations' daily rows, as `ByStationTable.read_stations` returns them.

    `year` is compared against every other year: its values are returned as they are, and each
    day's distribution is drawn from the rest. Days and observations are in calendar order, and
    series in the order of `station_codes`.
    """
    codes = list(dict.fromkeys(station_codes))
    by_station = _values_by_station(rows, variable)
    if method == ClimatologyMethod.EACH:
        series = [_series(by_station.get(code, {}), [code], year, pooled=False) for code in codes]
    else:
        merged = _merge([by_station[code] for code in codes if code in by_station])
        series = [_series(merged, codes, year, pooled=method == ClimatologyMethod.POOLED)]
    return DailyClimatologyResponse(variable=variable, year=year, method=method, series=series)
