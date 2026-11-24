"""Weather model forecasts at any location in BC, for the public Station Weather API.

They are read from the model grids: `recent` holds every run for two days, and `history` one run
a day, kept. Which of the two a run comes from makes no difference to a caller.
"""

import asyncio
import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

import pyarrow as pa
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field
from wps_weather_data.grids.grib import BC_LATITUDE, BC_LONGITUDE
from wps_weather_data.grids.models import MODELS
from wps_weather_data.grids.point import read_point_forecast
from wps_weather_data.grids.store import GridStore

from app.weather_rows import CSV_RESPONSE, csv_response, rounded, wants_csv

logger = logging.getLogger(__name__)

router = APIRouter()

# How many grid reads run at once. Each reads its arrays in 20 threads, and the rest wait.
CONCURRENT_READS = 4
_reads = asyncio.Semaphore(CONCURRENT_READS)

# Not the station values' models: NAM has no grids. Named as they are stored.
GridModelName = StrEnum("GridModelName", {name: name for name in MODELS})

# A model's `recent` and `history` stores.
ModelStores = tuple[GridStore, GridStore]


class GridRun(BaseModel):
    run_timestamp: datetime = Field(description="UTC start of the model run")
    last_forecast_hour: int = Field(description="How many hours ahead the run forecasts")


class GridRunsResponse(BaseModel):
    model: GridModelName
    runs: list[GridRun] = Field(description="Newest first")


class PointRow(BaseModel):
    timestamp: datetime = Field(description="UTC time the values are for")
    run_timestamp: datetime = Field(description="UTC start of the model run the values are from")
    forecast_hour: int = Field(description="Hours since the run started")
    temperature: float | None = Field(description="Air temperature, °C")
    relative_humidity: float | None = Field(description="Relative humidity, %")
    wind_speed: float | None = Field(description="Wind speed, km/h")
    wind_direction: float | None = Field(description="Wind direction, degrees")
    precipitation: float | None = Field(description="Precipitation since the row before, mm")


class PointForecastResponse(BaseModel):
    model: GridModelName
    latitude: float = Field(description="Latitude of the grid cell the values are from")
    longitude: float = Field(description="Longitude of the grid cell the values are from")
    rows: list[PointRow] = Field(description="Sorted by time")


class RunNotFoundError(Exception):
    pass


def get_grid_stores(request: Request) -> dict[str, ModelStores]:
    return request.app.state.grid_stores


ModelName = Annotated[GridModelName, Path(description="The weather model")]
GridStores = Annotated[dict[str, ModelStores], Depends(get_grid_stores)]


async def _read(function, *args):
    """Run a grid read, which blocks on the network, in a thread."""
    async with _reads:
        return await asyncio.to_thread(function, *args)


def model_runs(stores: ModelStores) -> dict[datetime, GridStore]:
    """Every run of a model that is kept, and the store to read it from."""
    recent, history = stores
    return {run_time: store for store in (history, recent) for run_time in store.run_times()}


def read_point(
    stores: ModelStores, run_time: datetime | None, latitude: float, longitude: float
) -> tuple[float, float, pa.Table]:
    """The forecast of a run, or of the newest, at the grid cell nearest a location: the cell's
    latitude and longitude, and a row per forecast hour."""
    runs = model_runs(stores)
    if run_time is None:
        run_time = max(runs, default=None)
    if run_time not in runs:
        raise RunNotFoundError
    store = runs[run_time]
    y, x = store.nearest_cell(latitude, longitude)
    latitudes, longitudes = store.coordinates
    rows = read_point_forecast(store, run_time, y, x)
    return float(latitudes[y, x]), float(longitudes[y, x]), rounded(rows)


@router.get(
    "/grids/{model}/runs",
    response_model=GridRunsResponse,
    tags=["Grids"],
    summary="List a model's runs",
    description="The runs of a weather model whose grids are kept: every run of the last two "
    "days, and one run a day before that, from November 2026.",
    responses=CSV_RESPONSE,
)
async def get_grid_runs(request: Request, model: ModelName, grid_stores: GridStores):
    runs = await _read(model_runs, grid_stores[model])
    rows = [
        {
            "run_timestamp": run_time,
            "last_forecast_hour": MODELS[model].forecast_hours(run_time)[-1],
        }
        for run_time in sorted(runs, reverse=True)
    ]
    if wants_csv(request):
        schema = pa.schema(
            [("run_timestamp", pa.timestamp("us", tz="UTC")), ("last_forecast_hour", pa.int32())]
        )
        return csv_response(pa.Table.from_pylist(rows, schema=schema), {})
    return {"model": model, "runs": rows}


@router.get(
    "/grids/{model}/point",
    response_model=PointForecastResponse,
    tags=["Grids"],
    summary="Get a model's forecast at a location",
    description="""
A weather model's forecast at the grid cell nearest a location in BC, with a row for each forecast
hour. Without `run_timestamp`, from the newest run.

The values are the model's own, with no bias adjustment, in the same units for every model. HRDPS
and RDPS have a row an hour. GDPS and GFS have one every 3 hours, and ECMWF every 3 hours, then
every 6 after hour 144. Send `Accept: text/csv` for CSV instead of JSON.
""",
    responses={
        **CSV_RESPONSE,
        404: {"description": "The run is not kept"},
        422: {"description": "Invalid parameters"},
    },
)
async def get_point_forecast(
    request: Request,
    model: ModelName,
    grid_stores: GridStores,
    latitude: Annotated[
        float,
        Query(ge=BC_LATITUDE[0], le=BC_LATITUDE[1], description="Degrees north", examples=[50.7]),
    ],
    longitude: Annotated[
        float,
        Query(
            ge=BC_LONGITUDE[0],
            le=BC_LONGITUDE[1],
            description="Degrees east, so negative in BC",
            examples=[-120.44],
        ),
    ],
    run_timestamp: Annotated[
        datetime | None,
        Query(
            description="UTC start of the model run, one of those listed by `runs`",
            examples=["2026-11-23T18:00:00Z"],
        ),
    ] = None,
):
    if run_timestamp is not None and run_timestamp.tzinfo is None:
        run_timestamp = run_timestamp.replace(tzinfo=UTC)
    logger.info("Weather grids: %s run %s", model, run_timestamp or "newest")
    try:
        cell_latitude, cell_longitude, rows = await _read(
            read_point, grid_stores[model], run_timestamp, latitude, longitude
        )
    except RunNotFoundError:
        asked_for = "runs" if run_timestamp is None else f"run {run_timestamp.isoformat()}"
        raise HTTPException(404, f"No {model} {asked_for} kept")
    if wants_csv(request):
        return csv_response(rows, {})
    return {
        "model": model,
        "latitude": cell_latitude,
        "longitude": cell_longitude,
        "rows": rows.to_pylist(),
    }
