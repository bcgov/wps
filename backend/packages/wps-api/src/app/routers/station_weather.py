"""Historical and current station weather for the public Station Weather API.

Older rows come from `by_station`, which holds each station's whole record but is rebuilt
nightly, and the last few days from `by_time`, which the jobs write to as data arrives.
"""

import asyncio
import logging
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from typing import Annotated

import pyarrow as pa
import pyarrow.compute as pc
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field
from wps_shared.utils.time import get_utc_now
from wps_shared.weather_models import ModelEnum
from wps_weather_data.by_station import ByStationTable
from wps_weather_data.by_time import ACTUALS, FORECAST, HOURLY, VALUE_TYPES, ByTimeTable

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Station weather"])

MAX_STATIONS = 50
# The most rows a request may ask for: stations x days x sources, x 24 for hourly. It bounds
# the response at tens of MB.
MAX_ROWS = 50_000
# `by_station` is rebuilt nightly, so rows from this many UTC days back are read from `by_time`.
RECENT_DAYS = 2


class Resolution(StrEnum):
    HOURLY = "hourly"
    DAILY = "daily"


# Named as they are stored. (StrEnum's own values from a list of names would be lowercase.)
Source = StrEnum(
    "Source", {name: name for name in (ACTUALS, FORECAST, *(model.value for model in ModelEnum))}
)

_OUTPUT_COLUMNS = ["station_code", "source", "timestamp", *VALUE_TYPES, "run_ts"]


class StationWeatherRow(BaseModel):
    station_code: int
    source: Source = Field(description="ACTUALS, FORECAST, or the weather model")
    timestamp: datetime = Field(
        description="UTC time the values are for. Daily rows are at 20:00 UTC (noon PST)."
    )
    temperature: float | None = Field(description="Air temperature, °C")
    relative_humidity: float | None = Field(description="Relative humidity, %")
    wind_speed: float | None = Field(description="Wind speed, km/h")
    wind_direction: float | None = Field(description="Wind direction, degrees")
    precipitation: float | None = Field(
        description="Precipitation, mm: the hour's for hourly rows, the 24 hours before for daily"
    )
    bias_adjusted_temperature: float | None = Field(description="Models only, °C")
    bias_adjusted_relative_humidity: float | None = Field(description="Models only, %")
    bias_adjusted_wind_speed: float | None = Field(description="Models only, km/h")
    bias_adjusted_wind_direction: float | None = Field(description="Models only, degrees")
    bias_adjusted_precipitation: float | None = Field(description="Models, daily only, mm")
    ffmc: float | None = Field(description="Fine Fuel Moisture Code. ACTUALS and FORECAST only.")
    dmc: float | None = Field(description="Duff Moisture Code. Daily ACTUALS and FORECAST only.")
    dc: float | None = Field(description="Drought Code. Daily ACTUALS and FORECAST only.")
    isi: float | None = Field(description="Initial Spread Index. ACTUALS and FORECAST only.")
    bui: float | None = Field(description="Buildup Index. Daily ACTUALS and FORECAST only.")
    fwi: float | None = Field(description="Fire Weather Index. ACTUALS and FORECAST only.")
    dewpoint: float | None = Field(description="Dew point, °C. ACTUALS and FORECAST only.")
    wind_gust: float | None = Field(description="Wind gust, km/h. Hourly data mart ACTUALS only.")
    grass_curing: float | None = Field(description="Percent cured. Daily ACTUALS and FORECAST.")
    danger_rating: int | None = Field(description="Danger class 1 to 5. Daily ACTUALS only.")
    observation_valid: bool | None = Field(
        description="Whether WF1 accepted the observation. Null when the source does not say."
    )
    observation_valid_comment: str | None = Field(description="Why WF1 rejected it")
    run_timestamp: datetime | None = Field(description="The model run the values are from")


class StationWeatherResponse(BaseModel):
    resolution: Resolution
    start: date
    end: date
    sources: list[Source]
    station_codes: list[int]
    rows: list[StationWeatherRow] = Field(description="Sorted by station, source, then time")


def get_by_station_table(request: Request) -> ByStationTable:
    return request.app.state.by_station_table


def get_by_time_table(request: Request) -> ByTimeTable:
    return request.app.state.by_time_table


def _rounded(rows: pa.Table) -> pa.Table:
    """Values are stored as float32, which as float64 reads 21.299999237 for 21.3."""
    for index, field in enumerate(rows.schema):
        if field.type == pa.float32():
            rows = rows.set_column(
                index, field.name, pc.round(rows[field.name].cast(pa.float64()), 3)
            )
    return rows


def read_station_weather(
    by_station: ByStationTable,
    by_time: ByTimeTable,
    resolution: str,
    station_codes: list[int],
    sources: list[str],
    start: date,
    end: date,
    now: datetime,
) -> pa.Table:
    """The rows with a UTC date from `start` to `end`, sorted by station, source then time."""
    first = datetime.combine(start, time(), tzinfo=UTC)
    after_last = datetime.combine(end + timedelta(days=1), time(), tzinfo=UTC)
    recent = datetime.combine(now.date() - timedelta(days=RECENT_DAYS), time(), tzinfo=UTC)
    parts = []
    if first < recent:
        rows = by_station.read_stations(
            resolution, station_codes, sources, years=list(range(start.year, end.year + 1))
        )
        timestamps = rows["timestamp"]
        rows = rows.filter(
            pc.and_(
                pc.greater_equal(timestamps, pa.scalar(first)),
                pc.less(timestamps, pa.scalar(min(after_last, recent))),
            )
        )
        parts.append(rows.select(_OUTPUT_COLUMNS))
    if after_last > recent:
        rows = by_time.read(
            resolution,
            sources,
            max(first, recent),
            after_last - timedelta(microseconds=1),
            station_codes=station_codes,
        )
        parts.append(rows.select(_OUTPUT_COLUMNS))
    rows = pa.concat_tables(parts, promote_options="permissive")
    rows = rows.sort_by(
        [("station_code", "ascending"), ("source", "ascending"), ("timestamp", "ascending")]
    )
    return _rounded(rows).rename_columns({"run_ts": "run_timestamp"})


_DESCRIPTION = """
Observations (`ACTUALS`), forecasters' noon forecasts (`FORECAST`) and weather model values
(`GDPS`, `RDPS`, `HRDPS`, `GFS`, `NAM`, `ECMWF`) at BC Wildfire Service weather stations, for
UTC dates from `start` to `end` inclusive.

Hourly observations go back to 1987. Daily rows are at 20:00 UTC (noon PST). A model's row holds
the newest prediction made for that time. `FORECAST` holds only each day's latest forecast.

A request may cover at most 50,000 rows, counted as stations x days x sources, and x 24 for
hourly. Split larger requests by date.
"""


@router.get(
    "/{resolution}",
    response_model=StationWeatherResponse,
    summary="Get station weather for a date range",
    description=_DESCRIPTION,
    responses={422: {"description": "Invalid parameters, or the request covers too many rows"}},
)
async def get_station_weather(
    resolution: Annotated[Resolution, Path(description="`hourly` or `daily`")],
    station_codes: Annotated[
        list[int],
        Query(min_length=1, max_length=MAX_STATIONS, description="WF1 station codes"),
    ],
    start: Annotated[date, Query(description="First UTC date", examples=["2026-07-01"])],
    end: Annotated[date, Query(description="Last UTC date", examples=["2026-07-31"])],
    by_station: Annotated[ByStationTable, Depends(get_by_station_table)],
    by_time: Annotated[ByTimeTable, Depends(get_by_time_table)],
    sources: Annotated[list[Source], Query(description="Defaults to ACTUALS")] = [Source.ACTUALS],
):
    if end < start:
        raise HTTPException(status_code=422, detail="end is before start")
    station_codes = list(dict.fromkeys(station_codes))
    sources = list(dict.fromkeys(sources))
    days = (end - start).days + 1
    requested = len(station_codes) * len(sources) * days * (24 if resolution == HOURLY else 1)
    if requested > MAX_ROWS:
        raise HTTPException(
            status_code=422,
            detail=f"Request covers up to {requested} rows; the limit is {MAX_ROWS}",
        )
    logger.info(
        "Station weather: %s, %d stations, %s, %s to %s",
        resolution,
        len(station_codes),
        sources,
        start,
        end,
    )
    # The reads block on the network, so they run in a thread to keep the event loop free.
    rows = await asyncio.to_thread(
        read_station_weather,
        by_station,
        by_time,
        resolution,
        station_codes,
        [source.value for source in sources],
        start,
        end,
        get_utc_now(),
    )
    return StationWeatherResponse(
        resolution=resolution,
        start=start,
        end=end,
        sources=sources,
        station_codes=station_codes,
        rows=rows.to_pylist(),
    )
