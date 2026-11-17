"""Daily climatology for a station: how a variable has been distributed on each day of the year.

The values are the station's daily actuals, which are WF1's noon (20:00 UTC) records. One year
is held out to compare against the others, so a year in progress does not shift the
distribution it is being compared with.
"""

from collections import defaultdict

import numpy as np
import pyarrow as pa
from wps_shared.schemas.climatology import (
    ClimatologyDay,
    ClimatologyObservation,
    ClimatologyVariable,
    DailyClimatologyResponse,
)

# A leap day has a value in one year of four, too few to describe, so it is left out.
_LEAP_DAY = (2, 29)
_PERCENTILES = (0, 25, 50, 75, 90, 100)


def daily_climatology(
    rows: pa.Table, station_code: int, variable: ClimatologyVariable, year: int
) -> DailyClimatologyResponse:
    """Summarize a station's daily rows, as `ByStationTable.read` returns them.

    `year` is compared against every other year: its values are returned as they are, and each
    day's distribution is drawn from the rest. Days and observations are in calendar order.
    """
    values_by_day: dict[tuple[int, int], list[float]] = defaultdict(list)
    observations: list[ClimatologyObservation] = []
    reference_years: set[int] = set()
    for timestamp, value in zip(
        rows["timestamp"].to_pylist(), rows[variable.value].to_pylist(), strict=True
    ):
        if value is None:
            continue
        # The daily record is at 20:00 UTC, noon PST, so the UTC date is the local date.
        day = timestamp.date()
        if day.year == year:
            observations.append(ClimatologyObservation(date=day, value=value))
        elif (day.month, day.day) != _LEAP_DAY:
            values_by_day[(day.month, day.day)].append(value)
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
                minimum=minimum,
                p25=p25,
                median=median,
                p75=p75,
                p90=p90,
                maximum=maximum,
            )
        )
    return DailyClimatologyResponse(
        station_code=station_code,
        variable=variable,
        year=year,
        first_reference_year=min(reference_years, default=None),
        last_reference_year=max(reference_years, default=None),
        days=days,
        observations=sorted(observations, key=lambda observation: observation.date),
    )
