"""Historical and current station weather for the public Station Weather API.

Each kind of data is its own resource, with only the fields it has: observations, forecasters'
noon forecasts, weather model values, and the stations themselves. Every resource returns JSON,
or CSV when asked for with `Accept: text/csv`.

Older rows come from `by_station`, which holds each station's whole record but is rebuilt
nightly, and the last few days from `by_time`, which the jobs write to as data arrives. The
stations come from `stations`, which the hourly actuals job copies from WF1.
"""

import asyncio
import io
import logging
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from typing import Annotated

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv
from fastapi import APIRouter, Depends, Path, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from wps_shared.utils.time import get_utc_now
from wps_shared.weather_models import ModelEnum
from wps_weather_data.by_station import ByStationTable
from wps_weather_data.by_time import ACTUALS, DAILY, FORECAST, HOURLY, ByTimeTable
from wps_weather_data.stations import StationsTable

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_STATIONS = 50
# The most rows a page holds, counted as stations x days, x 24 for hourly. It bounds a response
# at tens of MB. A page is whole days, so it holds at least one day for every station.
PAGE_ROWS = 50_000
# `by_station` is rebuilt nightly, so rows from this many UTC days back are read from `by_time`.
RECENT_DAYS = 2
# The dates a request covers when it does not say: the last week of observations, and the next
# ten days of forecasts and model values.
DEFAULT_PAST_DAYS = 7
DEFAULT_FUTURE_DAYS = 10

CSV = "text/csv"


class Resolution(StrEnum):
    HOURLY = HOURLY
    DAILY = DAILY


# Named as they are stored. (StrEnum's own values from a list of names would be lowercase.)
Model = StrEnum("Model", {model.value: model.value for model in ModelEnum})


_TIME = "UTC time the values are for. Daily rows are at 20:00 UTC (noon PST)."


class ObservationRow(BaseModel):
    station_code: int
    timestamp: datetime = Field(description=_TIME)
    temperature: float | None = Field(description="Air temperature, °C")
    relative_humidity: float | None = Field(description="Relative humidity, %")
    dewpoint: float | None = Field(description="Dew point, °C")
    wind_speed: float | None = Field(description="Wind speed, km/h")
    wind_direction: float | None = Field(description="Wind direction, degrees")
    wind_gust: float | None = Field(description="Wind gust, km/h. Hourly, back to 1987 only.")
    precipitation: float | None = Field(
        description="Precipitation, mm: the hour's for hourly rows, the 24 hours before for daily"
    )
    ffmc: float | None = Field(description="Fine Fuel Moisture Code")
    dmc: float | None = Field(description="Duff Moisture Code. Daily only.")
    dc: float | None = Field(description="Drought Code. Daily only.")
    isi: float | None = Field(description="Initial Spread Index")
    bui: float | None = Field(description="Buildup Index. Daily only.")
    fwi: float | None = Field(description="Fire Weather Index")
    grass_curing: float | None = Field(description="Grass curing, %. Daily only.")
    danger_rating: int | None = Field(description="Forest danger class, 1 to 5. Daily only.")
    observation_valid: bool | None = Field(
        description="Whether WF1 accepted the observation. Null for history that does not say."
    )
    observation_valid_comment: str | None = Field(description="Why WF1 did not accept it")


class ForecastRow(BaseModel):
    station_code: int
    timestamp: datetime = Field(description="Forecasts are for 20:00 UTC (noon PST)")
    temperature: float | None = Field(description="Air temperature, °C")
    relative_humidity: float | None = Field(description="Relative humidity, %")
    dewpoint: float | None = Field(description="Dew point, °C")
    wind_speed: float | None = Field(description="Wind speed, km/h")
    wind_direction: float | None = Field(description="Wind direction, degrees")
    precipitation: float | None = Field(description="Precipitation over the 24 hours before, mm")
    ffmc: float | None = Field(description="Fine Fuel Moisture Code")
    dmc: float | None = Field(description="Duff Moisture Code")
    dc: float | None = Field(description="Drought Code")
    isi: float | None = Field(description="Initial Spread Index")
    bui: float | None = Field(description="Buildup Index")
    fwi: float | None = Field(description="Fire Weather Index")
    grass_curing: float | None = Field(description="Grass curing, %")


class ModelRow(BaseModel):
    station_code: int
    timestamp: datetime = Field(description=_TIME)
    run_timestamp: datetime = Field(description="UTC start of the model run the values are from")
    temperature: float | None = Field(description="Air temperature, °C")
    relative_humidity: float | None = Field(description="Relative humidity, %")
    wind_speed: float | None = Field(description="Wind speed, km/h")
    wind_direction: float | None = Field(description="Wind direction, degrees")
    precipitation: float | None = Field(
        description="Precipitation, mm: the hour's for hourly rows, the 24 hours before for daily"
    )
    bias_adjusted_temperature: float | None = Field(description="°C")
    bias_adjusted_relative_humidity: float | None = Field(description="%")
    bias_adjusted_wind_speed: float | None = Field(description="km/h")
    bias_adjusted_wind_direction: float | None = Field(description="Degrees")
    bias_adjusted_precipitation: float | None = Field(description="Daily only, mm")


class Station(BaseModel):
    station_code: int
    name: str | None
    latitude: float | None
    longitude: float | None
    elevation: float | None = Field(description="Metres above sea level")
    status: str | None = Field(description="ACTIVE, TEST or PROJECT")


_NEXT = 'The URL of the next page, or null on the last. Also sent as a `Link: rel="next"` header.'
_PAGE_DATE = "this page covers. Later pages continue to the `end` asked for."


class StationsResponse(BaseModel):
    stations: list[Station] = Field(description="Sorted by station code")


class ObservationsResponse(BaseModel):
    resolution: Resolution
    start: date = Field(description=f"The first UTC date {_PAGE_DATE}")
    end: date = Field(description=f"The last UTC date {_PAGE_DATE}")
    station_codes: list[int]
    rows: list[ObservationRow] = Field(description="Sorted by station, then time")
    next: str | None = Field(description=_NEXT)


class ForecastsResponse(BaseModel):
    start: date = Field(description=f"The first UTC date {_PAGE_DATE}")
    end: date = Field(description=f"The last UTC date {_PAGE_DATE}")
    station_codes: list[int]
    rows: list[ForecastRow] = Field(description="Sorted by station, then time")
    next: str | None = Field(description=_NEXT)


class ModelValuesResponse(BaseModel):
    model: Model
    resolution: Resolution
    start: date = Field(description=f"The first UTC date {_PAGE_DATE}")
    end: date = Field(description=f"The last UTC date {_PAGE_DATE}")
    station_codes: list[int]
    rows: list[ModelRow] = Field(description="Sorted by station, then time")
    next: str | None = Field(description=_NEXT)


def get_by_station_table(request: Request) -> ByStationTable:
    return request.app.state.by_station_table


def get_by_time_table(request: Request) -> ByTimeTable:
    return request.app.state.by_time_table


def get_stations_table(request: Request) -> StationsTable:
    return request.app.state.stations_table


def _invalid(parameter: str, value, message: str) -> RequestValidationError:
    """A 422 in FastAPI's own shape, the same as its checks of the parameters' types return:
    `{"detail": [{"type", "loc", "msg", "input"}]}`."""
    return RequestValidationError(
        [{"type": "value_error", "loc": ("query", parameter), "msg": message, "input": value}]
    )


def station_codes_param(
    station_codes: Annotated[
        list[str],
        Query(
            min_length=1,
            description=(
                f"WF1 station codes, up to {MAX_STATIONS}: comma-separated, repeated, or both"
            ),
            examples=["322,209"],
        ),
    ],
) -> list[int]:
    """The station codes asked for, in order and without repeats."""
    try:
        codes = [int(code) for value in station_codes for code in value.split(",") if code.strip()]
    except ValueError:
        raise _invalid("station_codes", station_codes, "Station codes must be whole numbers")
    codes = list(dict.fromkeys(codes))
    if not codes or len(codes) > MAX_STATIONS:
        raise _invalid(
            "station_codes",
            station_codes,
            f"Ask for 1 to {MAX_STATIONS} stations, not {len(codes)}",
        )
    return codes


StationCodes = Annotated[list[int], Depends(station_codes_param)]
Start = Annotated[date | None, Query(description="First UTC date", examples=["2026-07-01"])]
End = Annotated[date | None, Query(description="Last UTC date", examples=["2026-07-31"])]


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
    source: str,
    start: date,
    end: date,
    now: datetime,
    columns: list[str],
) -> pa.Table:
    """A source's `columns` with a UTC date from `start` to `end`, sorted by station then time.
    `run_timestamp` is the stored `run_ts`."""
    stored = ["run_ts" if column == "run_timestamp" else column for column in columns]
    first = datetime.combine(start, time(), tzinfo=UTC)
    after_last = datetime.combine(end + timedelta(days=1), time(), tzinfo=UTC)
    recent = datetime.combine(now.date() - timedelta(days=RECENT_DAYS), time(), tzinfo=UTC)
    parts = []
    if first < recent:
        rows = by_station.read_stations(
            resolution, station_codes, [source], years=list(range(start.year, end.year + 1))
        )
        timestamps = rows["timestamp"]
        rows = rows.filter(
            pc.and_(
                pc.greater_equal(timestamps, pa.scalar(first)),
                pc.less(timestamps, pa.scalar(min(after_last, recent))),
            )
        )
        parts.append(rows.select(stored))
    if after_last > recent:
        rows = by_time.read(
            resolution,
            [source],
            max(first, recent),
            after_last - timedelta(microseconds=1),
            station_codes=station_codes,
        )
        parts.append(rows.select(stored))
    rows = pa.concat_tables(parts, promote_options="permissive")
    rows = rows.sort_by([("station_code", "ascending"), ("timestamp", "ascending")])
    return _rounded(rows).rename_columns(columns)


def _dates(start: date | None, end: date | None, today: date, ahead: bool) -> tuple[date, date]:
    """The dates asked for, filling in what is missing: the last week ending `end`, or for data
    that looks `ahead`, ten days from `start`."""
    if ahead:
        start = start or today
        end = end or start + timedelta(days=DEFAULT_FUTURE_DAYS - 1)
    else:
        end = end or today
        start = start or end - timedelta(days=DEFAULT_PAST_DAYS - 1)
    if end < start:
        raise _invalid("end", end, f"end is before start ({start})")
    return start, end


def _page_end(station_codes: list[int], start: date, end: date, resolution: str) -> date:
    """The last date of the page that starts at `start`: as many whole days as fit in
    `PAGE_ROWS`, and at least one."""
    rows_per_day = len(station_codes) * (24 if resolution == HOURLY else 1)
    days = max(1, PAGE_ROWS // rows_per_day)
    return min(end, start + timedelta(days=days - 1))


def _next_url(request: Request, page_end: date, end: date) -> str | None:
    """The same request from the day after this page, or None if this page reaches `end`. It is
    relative, so it holds behind the gateway, and names `end` so a default cannot move."""
    if page_end >= end:
        return None
    url = request.url.include_query_params(start=page_end + timedelta(days=1), end=end)
    return f"{url.path}?{url.query}"


def _wants_csv(request: Request) -> bool:
    return CSV in request.headers.get("accept", "")


def _csv(rows: pa.Table, headers: dict[str, str]) -> Response:
    """The rows as CSV, with times as ISO 8601 UTC like the JSON."""
    for index, field in enumerate(rows.schema):
        if pa.types.is_timestamp(field.type):
            # Arrow's %S has the fraction of a second too, unless the time is in seconds.
            seconds = rows[field.name].cast(pa.timestamp("s", tz="UTC"), safe=False)
            rows = rows.set_column(
                index, field.name, pc.strftime(seconds, format="%Y-%m-%dT%H:%M:%SZ")
            )
    buffer = io.BytesIO()
    pyarrow.csv.write_csv(rows, buffer)
    return Response(content=buffer.getvalue(), media_type=CSV, headers=headers)


_CSV_RESPONSE = {200: {"content": {CSV: {}}}}

_SIZE_NOTE = f"""
A long request comes back in pages of whole days, up to {PAGE_ROWS:,} rows each, counted as
stations x days, and x 24 for hourly. `start` and `end` in the response are the dates of the
page, and `next` is the URL of the next page, null on the last. The same URL is in the `Link`
header with `rel="next"`, for CSV too. Send `Accept: text/csv` for CSV instead of JSON.
"""


async def _rows_response(
    request: Request,
    response: Response,
    by_station: ByStationTable,
    by_time: ByTimeTable,
    *,
    source: str,
    resolution: str,
    station_codes: list[int],
    start: date | None,
    end: date | None,
    row_model: type[BaseModel],
    ahead: bool,
    **envelope,
):
    now = get_utc_now()
    start, end = _dates(start, end, now.date(), ahead)
    page_end = _page_end(station_codes, start, end, resolution)
    next_url = _next_url(request, page_end, end)
    headers = {"Link": f'<{next_url}>; rel="next"'} if next_url else {}
    logger.info(
        "Station weather: %s %s, %d stations, %s to %s",
        source,
        resolution,
        len(station_codes),
        start,
        page_end,
    )
    # The reads block on the network, so they run in a thread to keep the event loop free.
    rows = await asyncio.to_thread(
        read_station_weather,
        by_station,
        by_time,
        resolution,
        station_codes,
        source,
        start,
        page_end,
        now,
        list(row_model.model_fields),
    )
    if _wants_csv(request):
        return _csv(rows, headers)
    response.headers.update(headers)
    # Each response model keeps the fields it has: a forecast has no resolution.
    return {
        **envelope,
        "resolution": resolution,
        "start": start,
        "end": page_end,
        "station_codes": station_codes,
        "rows": rows.to_pylist(),
        "next": next_url,
    }


@router.get(
    "/stations",
    response_model=StationsResponse,
    tags=["Stations"],
    summary="List the weather stations",
    description="WF1's active, test and project weather stations, updated hourly. A station "
    "that has been decommissioned is not listed, but its history can still be requested.",
    responses=_CSV_RESPONSE,
)
async def get_stations(
    request: Request, stations: Annotated[StationsTable, Depends(get_stations_table)]
):
    rows = await asyncio.to_thread(stations.read)
    rows = rows.select(list(Station.model_fields))
    if _wants_csv(request):
        return _csv(rows, {})
    return {"stations": rows.to_pylist()}


@router.get(
    "/observations/{resolution}",
    response_model=ObservationsResponse,
    tags=["Observations"],
    summary="Get observations",
    description=f"""
Hourly or daily observations at weather stations, back to 1987, for UTC dates from `start` to
`end` inclusive. Without dates, the last {DEFAULT_PAST_DAYS} days.

Daily rows are WF1's daily record at 20:00 UTC (noon PST), with the 24 hour precipitation and
the FWI System indices.
{_SIZE_NOTE}""",
    responses={**_CSV_RESPONSE, 422: {"description": "Invalid parameters"}},
)
async def get_observations(
    request: Request,
    response: Response,
    resolution: Annotated[Resolution, Path(description="`hourly` or `daily`")],
    station_codes: StationCodes,
    by_station: Annotated[ByStationTable, Depends(get_by_station_table)],
    by_time: Annotated[ByTimeTable, Depends(get_by_time_table)],
    start: Start = None,
    end: End = None,
):
    return await _rows_response(
        request,
        response,
        by_station,
        by_time,
        source=ACTUALS,
        resolution=resolution,
        station_codes=station_codes,
        start=start,
        end=end,
        row_model=ObservationRow,
        ahead=False,
    )


@router.get(
    "/forecasts/daily",
    response_model=ForecastsResponse,
    tags=["Forecasts"],
    summary="Get forecasters' noon forecasts",
    description=f"""
BC Wildfire Service forecasters' noon forecasts at weather stations, for UTC dates from `start`
to `end` inclusive. Without dates, the {DEFAULT_FUTURE_DAYS} days from today. Each day holds its
latest forecast.
{_SIZE_NOTE}""",
    responses={**_CSV_RESPONSE, 422: {"description": "Invalid parameters"}},
)
async def get_forecasts(
    request: Request,
    response: Response,
    station_codes: StationCodes,
    by_station: Annotated[ByStationTable, Depends(get_by_station_table)],
    by_time: Annotated[ByTimeTable, Depends(get_by_time_table)],
    start: Start = None,
    end: End = None,
):
    return await _rows_response(
        request,
        response,
        by_station,
        by_time,
        source=FORECAST,
        resolution=DAILY,
        station_codes=station_codes,
        start=start,
        end=end,
        row_model=ForecastRow,
        ahead=True,
    )


@router.get(
    "/models/{model}/{resolution}",
    response_model=ModelValuesResponse,
    tags=["Models"],
    summary="Get weather model values",
    description=f"""
A weather model's values at weather stations, for UTC dates from `start` to `end` inclusive.
Without dates, the {DEFAULT_FUTURE_DAYS} days from today. Each time holds the newest prediction
made for it, and `run_timestamp` says which run that was.
{_SIZE_NOTE}""",
    responses={**_CSV_RESPONSE, 422: {"description": "Invalid parameters"}},
)
async def get_model_values(
    request: Request,
    response: Response,
    model: Annotated[Model, Path(description="The weather model")],
    resolution: Annotated[Resolution, Path(description="`hourly` or `daily`")],
    station_codes: StationCodes,
    by_station: Annotated[ByStationTable, Depends(get_by_station_table)],
    by_time: Annotated[ByTimeTable, Depends(get_by_time_table)],
    start: Start = None,
    end: End = None,
):
    return await _rows_response(
        request,
        response,
        by_station,
        by_time,
        source=model.value,
        resolution=resolution,
        station_codes=station_codes,
        start=start,
        end=end,
        row_model=ModelRow,
        ahead=True,
        model=model,
    )
