"""Climatology Router

Provides endpoints for calculating climate normals and comparing current year data
to historical averages across weather stations.
"""

from __future__ import annotations

import asyncio
import logging

import pyarrow as pa
from fastapi import APIRouter, HTTPException

from app.climatology import (
    DATE_COLUMN,
    compute_climatology,
    get_comparison_year_data,
    get_station_info,
)
from wps_shared.schemas.climatology import (
    ClimatologyDataPoint,
    ClimatologyRequest,
    ClimatologyResponse,
    ComparisonYearDataPoint,
    WeatherVariable,
)
from wps_shared.utils.delta import DeltaTableWrapper

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/climatology",
)


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
    precomputed_task = DeltaTableWrapper.load_climatology_stats(
        station_code=request.station_code,
        start_year=request.reference_period.start_year,
        end_year=request.reference_period.end_year,
    )
    station_task = get_station_info(request.station_code)

    # If we have a comparison year, load that data in parallel too
    comparison_task = None
    if comparison_year:
        comparison_task = DeltaTableWrapper.load_observations(
            station_code=request.station_code,
            start_year=comparison_year,
            end_year=comparison_year,
            columns=[DATE_COLUMN, column],
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
        obs_table = await DeltaTableWrapper.load_observations(
            station_code=request.station_code,
            start_year=request.reference_period.start_year,
            end_year=request.reference_period.end_year,
            columns=[DATE_COLUMN, column],
        )
        climatology = compute_climatology(obs_table, column, request.aggregation)

    # Extract comparison year data if loaded
    comparison_year_data: list[ComparisonYearDataPoint] = []
    if comparison_year and comparison_table is not None:
        comparison_year_data = get_comparison_year_data(comparison_table, column, request.aggregation)

    return ClimatologyResponse(
        climatology=climatology,
        comparison_year_data=comparison_year_data,
        station=station_info,
        variable=request.variable,
        aggregation=request.aggregation,
        reference_period=request.reference_period,
        comparison_year=comparison_year,
    )
