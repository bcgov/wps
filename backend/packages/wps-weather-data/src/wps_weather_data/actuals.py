"""Station observations (`ACTUALS`) read from `by_time`, for the model jobs.

Bias adjustment learns from the observations, and a run's first day of 24 hour precip adds the
precip observed before the run started. Both read a window of hourly observations once per run
being processed, and share it across stations.

Design: docs/architecture/station-weather-storage.md
"""

import logging
from bisect import bisect_left, bisect_right
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from wps_weather_data.by_time import ACTUALS, HOURLY, ByTimeTable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Observation:
    """One hourly observation at a station. A value WF1 did not have, or that was out of range,
    is None."""

    weather_date: datetime
    temperature: float | None
    relative_humidity: float | None
    wind_speed: float | None
    wind_direction: float | None
    precipitation: float | None


@dataclass(frozen=True)
class ObservedDailyPrecip:
    """The precip observed in the 24 hours ending at `day`."""

    day: datetime
    actual_precip_24h: float | None


class StationObservations:
    """Hourly observations per station, in time order."""

    def __init__(self, by_station: dict[int, list[Observation]]):
        self._by_station = by_station
        self._times = {
            station_code: [observation.weather_date for observation in observations]
            for station_code, observations in by_station.items()
        }

    @classmethod
    def read(cls, by_time: ByTimeTable, start: datetime, end: datetime) -> "StationObservations":
        """Read every station's observations for times in [start, end]."""
        rows = by_time.read(HOURLY, [ACTUALS], start, end)
        by_station: dict[int, list[Observation]] = defaultdict(list)
        for row in rows.to_pylist():
            by_station[row["station_code"]].append(
                Observation(
                    weather_date=row["timestamp"],
                    temperature=row["temperature"],
                    relative_humidity=row["relative_humidity"],
                    wind_speed=row["wind_speed"],
                    wind_direction=row["wind_direction"],
                    precipitation=row["precipitation"],
                )
            )
        logger.info("Read %d hourly observations from by_time", rows.num_rows)
        return cls(dict(by_station))

    def _between(self, station_code: int, start: datetime, end: datetime, *, include_start: bool):
        """The station's observations with a time from start to end, end included."""
        times = self._times.get(station_code, [])
        first = bisect_left(times, start) if include_start else bisect_right(times, start)
        last = bisect_right(times, end)
        return self._by_station.get(station_code, [])[first:last]

    def hourly(self, station_code: int, start: datetime, end: datetime) -> list[Observation]:
        """The station's observations in [start, end] with both a temperature and an RH."""
        return [
            observation
            for observation in self._between(station_code, start, end, include_start=True)
            if observation.temperature is not None and observation.relative_humidity is not None
        ]

    def accumulated_precip(self, station_code: int, start: datetime, end: datetime) -> float:
        """The precip observed in (start, end]. Hours with no precip value add nothing."""
        return sum(
            observation.precipitation
            for observation in self._between(station_code, start, end, include_start=False)
            if observation.precipitation is not None
        )

    def precip_by_24h(
        self, station_code: int, start: datetime, end: datetime
    ) -> list[ObservedDailyPrecip]:
        """The precip observed in the 24 hours ending at each of start, start + 24h, ... up to end.

        A day with no observations is left out. A day with an hour missing its precip has no
        total, rather than a total that is too low.
        """
        totals = []
        day = start
        while day <= end:
            hours = self._between(station_code, day - timedelta(hours=24), day, include_start=False)
            if hours:
                precip = [observation.precipitation for observation in hours]
                total = None if None in precip else sum(precip)
                totals.append(ObservedDailyPrecip(day, total))
            day += timedelta(hours=24)
        return totals


def get_accumulated_precipitation(
    observations: StationObservations, station_code: int, start: datetime, end: datetime
) -> float:
    """The precip observed at the station in (start, end]."""
    return observations.accumulated_precip(station_code, start, end)
