"""Climatology Router

Provides endpoints for calculating climate normals and comparing current year data
to historical averages across weather stations.
"""

from __future__ import annotations

import asyncio
import logging

import pyarrow as pa
import pyarrow.compute as pc
from fastapi import APIRouter, HTTPException

from wps_shared.schemas.climatology import (
    AggregationPeriod,
    ClimatologyDataPoint,
    ClimatologyRequest,
    ClimatologyResponse,
    CurrentYearDataPoint,
    StationInfo,
    WeatherVariable,
)
from wps_shared.utils.delta import DeltaTableWrapper

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/climatology",
)


# Delta Lake column names
DATE_COLUMN = "DATE_TIME"
STATION_CODE_COLUMN = "STATION_CODE"



async def load_precomputed_climatology(
    station_code: int,
    start_year: int,
    end_year: int,
) -> pa.Table | None:
    """Load pre-computed climatology stats from Delta Lake."""
    return await DeltaTableWrapper.load_climatology_stats(
        station_code=station_code,
        start_year=start_year,
        end_year=end_year,
    )


async def load_observations(
    station_code: int,
    start_year: int,
    end_year: int,
    column: str,
) -> pa.Table:
    """Load observations from Delta Lake for the specified station and year range."""
    try:
        return await DeltaTableWrapper.load_observations(
            station_code=station_code,
            start_year=start_year,
            end_year=end_year,
            columns=[DATE_COLUMN, column],
        )
    except Exception as e:
        logger.error(f"Error loading observations from Delta Lake: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading observations: {str(e)}")


# Cache for station info - stations rarely change
_station_cache: dict[int, StationInfo] = {}


async def get_station_info(station_code: int) -> StationInfo:
    """Get station information from Delta Lake with caching."""
    # Check cache first
    if station_code in _station_cache:
        return _station_cache[station_code]

    try:
        table = await DeltaTableWrapper.load_station(
            station_code=station_code,
            columns=["STATION_CODE", "STATION_NAME", "ELEVATION_M"],
        )

        if table.num_rows == 0:
            return StationInfo(
                code=station_code,
                name=f"Station {station_code}",
                elevation=None,
            )

        # Extract first row values using PyArrow
        name_val = table.column("STATION_NAME")[0].as_py()
        elev_val = table.column("ELEVATION_M")[0].as_py()

        name = name_val if name_val is not None else f"Station {station_code}"
        elevation = int(elev_val) if elev_val is not None else None

        result = StationInfo(
            code=station_code,
            name=name,
            elevation=elevation,
        )
        _station_cache[station_code] = result
        return result

    except Exception as e:
        logger.warning(f"Could not fetch station info for {station_code}: {e}")
        return StationInfo(
            code=station_code,
            name=f"Station {station_code}",
            elevation=None,
        )


def compute_climatology(
    table: pa.Table,
    column: str,
    aggregation: AggregationPeriod,
) -> list[ClimatologyDataPoint]:
    """Compute climatology statistics from observations using PyArrow."""
    if table.num_rows == 0:
        return []

    # Extract period (day of year or month) from timestamp
    timestamps = table.column(DATE_COLUMN)
    if aggregation == AggregationPeriod.DAILY:
        period_arr = pc.day_of_year(timestamps)
        period_range = range(1, 367)
    else:
        period_arr = pc.month(timestamps)
        period_range = range(1, 13)

    # Add period column to table
    table = table.append_column("period", period_arr)
    values_col = table.column(column)

    # Group by period and compute stats
    # Using PyArrow's group_by for aggregation
    stats_by_period: dict[int, dict[str, float | None]] = {}

    for period in period_range:
        # Filter to this period
        mask = pc.equal(table.column("period"), period)
        period_values = pc.filter(values_col, mask)

        # Drop nulls and compute stats
        valid_values = pc.drop_null(period_values)

        if len(valid_values) == 0:
            stats_by_period[period] = {
                "mean": None,
                "p10": None,
                "p25": None,
                "p50": None,
                "p75": None,
                "p90": None,
            }
        else:
            stats_by_period[period] = {
                "mean": pc.mean(valid_values).as_py(),
                "p10": pc.quantile(valid_values, q=0.10)[0].as_py(),
                "p25": pc.quantile(valid_values, q=0.25)[0].as_py(),
                "p50": pc.quantile(valid_values, q=0.50)[0].as_py(),
                "p75": pc.quantile(valid_values, q=0.75)[0].as_py(),
                "p90": pc.quantile(valid_values, q=0.90)[0].as_py(),
            }

    return [
        ClimatologyDataPoint(period=p, **stats_by_period.get(p, {}))
        for p in period_range
        if p in stats_by_period
    ]


def extract_current_year_data(
    table: pa.Table,
    column: str,
    aggregation: AggregationPeriod,
) -> list[CurrentYearDataPoint]:
    """Extract current year data from observations using PyArrow."""
    if table.num_rows == 0:
        return []

    timestamps = table.column(DATE_COLUMN)
    values_col = table.column(column)

    # Extract period (day of year or month)
    if aggregation == AggregationPeriod.DAILY:
        period_arr = pc.day_of_year(timestamps)
    else:
        period_arr = pc.month(timestamps)

    # Get unique periods and compute mean for each
    table = table.append_column("period", period_arr)
    unique_periods = pc.unique(period_arr).to_pylist()
    unique_periods.sort()

    results = []
    for period in unique_periods:
        if period is None:
            continue

        mask = pc.equal(table.column("period"), period)
        period_values = pc.filter(values_col, mask)
        period_timestamps = pc.filter(timestamps, mask)

        # Compute mean of values (dropping nulls)
        valid_values = pc.drop_null(period_values)
        if len(valid_values) > 0:
            mean_val = pc.mean(valid_values).as_py()
        else:
            mean_val = None

        # Get first date for this period
        first_ts = period_timestamps[0].as_py()
        date_str = first_ts.strftime("%Y-%m-%d") if first_ts else ""

        results.append(
            CurrentYearDataPoint(
                period=int(period),
                value=float(mean_val) if mean_val is not None else None,
                date=date_str,
            )
        )

    return results


@router.post("/", response_model=ClimatologyResponse)
async def get_climatology(request: ClimatologyRequest):
    """
    Get climatology data for a weather station.

    Returns percentile bands (p10, p25, p50, p75, p90) and mean values computed
    from the reference period, along with the current/comparison year data overlay.

    Uses pre-computed stats if available (much faster), otherwise computes on-the-fly.
    """
    logger.info(
        f"/climatology/ - station: {request.station_code}, variable: {request.variable.value}"
    )

    # Validate reference period
    if request.reference_period.start_year > request.reference_period.end_year:
        raise HTTPException(
            status_code=400,
            detail="Reference period start_year must be less than or equal to end_year",
        )

    column = request.variable.value
    comparison_year = request.comparison_year

    # Load precomputed stats, comparison year data, and station info in parallel
    precomputed_task = load_precomputed_climatology(
        station_code=request.station_code,
        start_year=request.reference_period.start_year,
        end_year=request.reference_period.end_year,
    )
    station_task = get_station_info(request.station_code)

    # If we have a comparison year, load that data in parallel too
    comparison_task = None
    if comparison_year:
        comparison_task = load_observations(
            station_code=request.station_code,
            start_year=comparison_year,
            end_year=comparison_year,
            column=column,
        )

    # Wait for all parallel tasks
    if comparison_task:
        precomputed, station_info, comparison_table = await asyncio.gather(
            precomputed_task, station_task, comparison_task
        )
    else:
        precomputed, station_info = await asyncio.gather(precomputed_task, station_task)
        comparison_table = None

    # Process precomputed stats or fall back to computing on-the-fly
    if precomputed is not None and precomputed.num_rows > 0:
        logger.info("Using pre-computed climatology stats")
        # Map variable to pre-computed column prefix
        var_prefix_map = {
            WeatherVariable.HOURLY_TEMPERATURE: "temp",
            WeatherVariable.HOURLY_RELATIVE_HUMIDITY: "rh",
            WeatherVariable.HOURLY_WIND_SPEED: "ws",
            WeatherVariable.HOURLY_PRECIPITATION: "precip",
            WeatherVariable.HOURLY_FINE_FUEL_MOISTURE_CODE: "ffmc",
            WeatherVariable.HOURLY_INITIAL_SPREAD_INDEX: "isi",
            WeatherVariable.HOURLY_FIRE_WEATHER_INDEX: "fwi",
        }
        prefix = var_prefix_map[request.variable]

        def get_column_values(tbl: pa.Table, col: str) -> list:
            if col in tbl.column_names:
                return tbl.column(col).to_pylist()
            return [None] * tbl.num_rows

        climatology = [
            ClimatologyDataPoint(
                period=int(day),
                mean=mean,
                p10=p10,
                p25=p25,
                p50=p50,
                p75=p75,
                p90=p90,
            )
            for day, mean, p10, p25, p50, p75, p90 in zip(
                precomputed.column("day_of_year").to_pylist(),
                get_column_values(precomputed, f"{prefix}_mean"),
                get_column_values(precomputed, f"{prefix}_p10"),
                get_column_values(precomputed, f"{prefix}_p25"),
                get_column_values(precomputed, f"{prefix}_p50"),
                get_column_values(precomputed, f"{prefix}_p75"),
                get_column_values(precomputed, f"{prefix}_p90"),
            )
        ]
    else:
        logger.info("Pre-computed stats not available, computing on-the-fly (slow)")
        # Fall back to computing on-the-fly
        obs_table = await load_observations(
            station_code=request.station_code,
            start_year=request.reference_period.start_year,
            end_year=request.reference_period.end_year,
            column=column,
        )
        climatology = compute_climatology(obs_table, column, request.aggregation)

    # Extract comparison year data if loaded
    current_year_data: list[CurrentYearDataPoint] = []
    if comparison_year and comparison_table is not None:
        current_year_data = extract_current_year_data(comparison_table, column, request.aggregation)

    return ClimatologyResponse(
        climatology=climatology,
        current_year=current_year_data,
        station=station_info,
        variable=request.variable,
        aggregation=request.aggregation,
        reference_period=request.reference_period,
        comparison_year=comparison_year,
    )
