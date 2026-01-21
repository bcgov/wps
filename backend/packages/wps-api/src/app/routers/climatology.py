"""Climatology Router

Provides endpoints for calculating climate normals and comparing current year data
to historical averages across weather stations.
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from wps_shared import config
from wps_shared.utils.delta import DeltaTableWrapper

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/climatology",
)


# --- Enums ---
class WeatherVariable(str, Enum):
    """Supported weather variables for climatology analysis."""

    HOURLY_TEMPERATURE = "HOURLY_TEMPERATURE"
    HOURLY_RELATIVE_HUMIDITY = "HOURLY_RELATIVE_HUMIDITY"
    HOURLY_WIND_SPEED = "HOURLY_WIND_SPEED"
    HOURLY_PRECIPITATION = "HOURLY_PRECIPITATION"
    HOURLY_FFMC = "HOURLY_FFMC"
    HOURLY_ISI = "HOURLY_ISI"
    HOURLY_FWI = "HOURLY_FWI"


class AggregationPeriod(str, Enum):
    """Time period for aggregating climatology data."""

    DAILY = "daily"
    MONTHLY = "monthly"


# Map weather variables to Delta Lake column names
VARIABLE_COLUMN_MAP = {
    WeatherVariable.HOURLY_TEMPERATURE: "HOURLY_TEMPERATURE",
    WeatherVariable.HOURLY_RELATIVE_HUMIDITY: "HOURLY_RELATIVE_HUMIDITY",
    WeatherVariable.HOURLY_WIND_SPEED: "HOURLY_WIND_SPEED",
    WeatherVariable.HOURLY_PRECIPITATION: "HOURLY_PRECIPITATION",
    WeatherVariable.HOURLY_FFMC: "HOURLY_FINE_FUEL_MOISTURE_CODE",
    WeatherVariable.HOURLY_ISI: "HOURLY_INITIAL_SPREAD_INDEX",
    WeatherVariable.HOURLY_FWI: "HOURLY_FIRE_WEATHER_INDEX",
}

# Delta Lake column names
DATE_COLUMN = "DATE_TIME"
STATION_CODE_COLUMN = "STATION_CODE"


# --- Request/Response Models ---
class ReferencePeriod(BaseModel):
    """Reference period for computing climate normals."""

    start_year: int = Field(..., ge=1950, le=2100, description="Start year of reference period")
    end_year: int = Field(..., ge=1950, le=2100, description="End year of reference period")


class ClimatologyRequest(BaseModel):
    """Request for climatology data."""

    station_code: int = Field(..., description="Weather station code")
    variable: WeatherVariable = Field(..., description="Weather variable to analyze")
    aggregation: AggregationPeriod = Field(
        default=AggregationPeriod.DAILY, description="Aggregation period"
    )
    reference_period: ReferencePeriod = Field(
        ..., description="Reference period for climate normals"
    )
    comparison_year: Optional[int] = Field(
        default=None, description="Year to compare against normals"
    )


class ClimatologyDataPoint(BaseModel):
    """A single data point in the climatology time series."""

    period: int = Field(..., description="Day of year (1-366) or month (1-12)")
    mean: Optional[float] = Field(None, description="Mean value")
    p10: Optional[float] = Field(None, description="10th percentile")
    p25: Optional[float] = Field(None, description="25th percentile")
    p50: Optional[float] = Field(None, description="50th percentile (median)")
    p75: Optional[float] = Field(None, description="75th percentile")
    p90: Optional[float] = Field(None, description="90th percentile")


class CurrentYearDataPoint(BaseModel):
    """A data point for the current/comparison year."""

    period: int = Field(..., description="Day of year (1-366) or month (1-12)")
    value: Optional[float] = Field(None, description="Observed value")
    date: str = Field(..., description="Date of observation (YYYY-MM-DD)")


class StationInfo(BaseModel):
    """Basic station information."""

    code: int
    name: str
    elevation: Optional[int] = None


class ClimatologyResponse(BaseModel):
    """Response containing climatology data and comparison year data."""

    climatology: list[ClimatologyDataPoint] = Field(default_factory=list)
    current_year: list[CurrentYearDataPoint] = Field(default_factory=list)
    station: StationInfo
    variable: WeatherVariable
    aggregation: AggregationPeriod
    reference_period: ReferencePeriod
    comparison_year: Optional[int] = None


# --- Helper Functions ---
def get_storage_options() -> dict[str, str]:
    """Get S3 storage options for delta-rs."""
    return {
        "AWS_ENDPOINT_URL": f"https://{config.get('OBJECT_STORE_SERVER')}",
        "AWS_ACCESS_KEY_ID": config.get("OBJECT_STORE_USER_ID"),
        "AWS_SECRET_ACCESS_KEY": config.get("OBJECT_STORE_SECRET"),
        "AWS_REGION": "us-east-1",
        "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
    }


def get_table_uri(table_key: str) -> str:
    """Get the S3 URI for a Delta table."""
    bucket = config.get("OBJECT_STORE_BUCKET")
    return f"s3://{bucket}/{table_key}"


# Lazy-initialized Delta table wrappers
_observations_table: DeltaTableWrapper | None = None
_stations_table: DeltaTableWrapper | None = None
_climatology_stats_table: DeltaTableWrapper | None = None


def get_observations_table() -> DeltaTableWrapper:
    """Get the observations Delta table wrapper."""
    global _observations_table
    if _observations_table is None:
        _observations_table = DeltaTableWrapper(
            table_uri=get_table_uri("historical/observations"),
            storage_options=get_storage_options(),
        )
    return _observations_table


def get_stations_table() -> DeltaTableWrapper:
    """Get the stations Delta table wrapper."""
    global _stations_table
    if _stations_table is None:
        _stations_table = DeltaTableWrapper(
            table_uri=get_table_uri("historical/stations"),
            storage_options=get_storage_options(),
        )
    return _stations_table


def get_climatology_stats_table() -> DeltaTableWrapper:
    """Get the climatology stats Delta table wrapper."""
    global _climatology_stats_table
    if _climatology_stats_table is None:
        _climatology_stats_table = DeltaTableWrapper(
            table_uri=get_table_uri("historical/climatology_stats"),
            storage_options=get_storage_options(),
        )
    return _climatology_stats_table


def compute_percentiles(values: np.ndarray) -> dict[str, Optional[float]]:
    """Compute percentile statistics for a set of values."""
    # Filter out NaN values
    valid_values = values[~np.isnan(values)]

    if len(valid_values) == 0:
        return {
            "mean": None,
            "p10": None,
            "p25": None,
            "p50": None,
            "p75": None,
            "p90": None,
        }

    return {
        "mean": float(np.mean(valid_values)),
        "p10": float(np.percentile(valid_values, 10)),
        "p25": float(np.percentile(valid_values, 25)),
        "p50": float(np.percentile(valid_values, 50)),
        "p75": float(np.percentile(valid_values, 75)),
        "p90": float(np.percentile(valid_values, 90)),
    }


async def load_precomputed_climatology(
    station_code: int,
    start_year: int,
    end_year: int,
) -> pa.Table | None:
    """Load pre-computed climatology stats from Delta Lake."""
    try:
        wrapper = get_climatology_stats_table()
        filter_expr = (
            (pc.field("station_code") == station_code)
            & (pc.field("ref_start_year") == start_year)
            & (pc.field("ref_end_year") == end_year)
        )
        return await wrapper.query_arrow_async(filter=filter_expr)
    except Exception as e:
        logger.warning(f"Pre-computed climatology not available: {e}")
        return None


async def load_observations(
    station_code: int,
    start_year: int,
    end_year: int,
    column: str,
) -> pa.Table:
    """Load observations from Delta Lake for the specified station and year range."""
    try:
        wrapper = get_observations_table()
        filter_expr = (
            (pc.field(STATION_CODE_COLUMN) == station_code)
            & (pc.field("year") >= start_year)
            & (pc.field("year") <= end_year)
        )
        return await wrapper.query_arrow_async(
            columns=[DATE_COLUMN, column],
            filter=filter_expr,
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
        wrapper = get_stations_table()
        filter_expr = pc.field("STATION_CODE") == station_code
        table = await wrapper.query_arrow_async(
            columns=["STATION_CODE", "STATION_NAME", "ELEVATION_M"],
            filter=filter_expr,
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


# --- Endpoints ---
@router.post("/precompute", response_model=dict)
async def precompute_climatology_stats(
    start_year: int = 1991,
    end_year: int = 2020,
):
    """
    Pre-compute climatology statistics for all stations and save to a Delta table.

    This creates a small, fast-to-query table with pre-aggregated percentiles.
    Run this once after data updates to refresh the climatology cache.
    """
    logger.info(f"/climatology/precompute - Computing stats for {start_year}-{end_year}")

    import pyarrow as pa
    from deltalake import write_deltalake

    stats_uri = get_table_uri("historical/climatology_stats")
    storage_options = get_storage_options()

    try:
        obs_table = get_observations_table()

        # Filter to reference period
        filter_expr = (pc.field("year") >= start_year) & (pc.field("year") <= end_year)

        # Load filtered data
        columns = [
            STATION_CODE_COLUMN,
            DATE_COLUMN,
            "HOURLY_TEMPERATURE",
            "HOURLY_RELATIVE_HUMIDITY",
            "HOURLY_WIND_SPEED",
            "HOURLY_PRECIPITATION",
            "HOURLY_FINE_FUEL_MOISTURE_CODE",
            "HOURLY_INITIAL_SPREAD_INDEX",
            "HOURLY_FIRE_WEATHER_INDEX",
        ]

        logger.info("Loading observations for reference period...")
        df = obs_table.query(columns=columns, filter=filter_expr)
        logger.info(f"Loaded {len(df)} observations")

        # Add day_of_year column
        df["day_of_year"] = pd.to_datetime(df[DATE_COLUMN]).dt.dayofyear

        # Define aggregation function
        def compute_stats(group):
            result = {}
            for var, prefix in [
                ("HOURLY_TEMPERATURE", "temp"),
                ("HOURLY_RELATIVE_HUMIDITY", "rh"),
                ("HOURLY_WIND_SPEED", "ws"),
                ("HOURLY_PRECIPITATION", "precip"),
                ("HOURLY_FINE_FUEL_MOISTURE_CODE", "ffmc"),
                ("HOURLY_INITIAL_SPREAD_INDEX", "isi"),
                ("HOURLY_FIRE_WEATHER_INDEX", "fwi"),
            ]:
                values = group[var].dropna()
                if len(values) > 0:
                    result[f"{prefix}_mean"] = values.mean()
                    result[f"{prefix}_p10"] = np.percentile(values, 10)
                    result[f"{prefix}_p25"] = np.percentile(values, 25)
                    result[f"{prefix}_p50"] = np.percentile(values, 50)
                    result[f"{prefix}_p75"] = np.percentile(values, 75)
                    result[f"{prefix}_p90"] = np.percentile(values, 90)
                else:
                    for suffix in ["mean", "p10", "p25", "p50", "p75", "p90"]:
                        result[f"{prefix}_{suffix}"] = None
            return pd.Series(result)

        logger.info("Computing climatology statistics...")
        stats_df = (
            df.groupby([STATION_CODE_COLUMN, "day_of_year"])
            .apply(compute_stats, include_groups=False)
            .reset_index()
        )
        stats_df = stats_df.rename(columns={STATION_CODE_COLUMN: "station_code"})
        stats_df["ref_start_year"] = start_year
        stats_df["ref_end_year"] = end_year

        logger.info(f"Computed {len(stats_df)} climatology records")

        # Save to Delta table
        result_table = pa.Table.from_pandas(stats_df)
        write_deltalake(
            stats_uri,
            result_table,
            mode="overwrite",
            storage_options=storage_options,
        )

        logger.info(f"Saved climatology stats to {stats_uri}")

        return {
            "status": "success",
            "records": len(stats_df),
            "reference_period": f"{start_year}-{end_year}",
            "table": stats_uri,
        }

    except Exception as e:
        logger.error(f"Error pre-computing climatology: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pre-computation failed: {str(e)}")


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

    column = VARIABLE_COLUMN_MAP[request.variable]
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
            WeatherVariable.HOURLY_FFMC: "ffmc",
            WeatherVariable.HOURLY_ISI: "isi",
            WeatherVariable.HOURLY_FWI: "fwi",
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
        current_year_data = extract_current_year_data(
            comparison_table, column, request.aggregation
        )

    return ClimatologyResponse(
        climatology=climatology,
        current_year=current_year_data,
        station=station_info,
        variable=request.variable,
        aggregation=request.aggregation,
        reference_period=request.reference_period,
        comparison_year=comparison_year,
    )
