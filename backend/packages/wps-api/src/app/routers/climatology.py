"""Climatology Router

Provides endpoints for calculating climate normals and comparing current year data
to historical averages across weather stations.
"""

from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum
from typing import TYPE_CHECKING, Optional

import numpy as np
import pandas as pd
from deltalake import DeltaTable
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    import pyarrow.dataset

from wps_shared import config

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


# Cache for Delta datasets - avoids re-reading Delta log on every request
_dataset_cache: dict[str, pyarrow.dataset.Dataset] = {}
_dataset_cache_time: dict[str, float] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes


def get_cached_dataset(table_key: str) -> pyarrow.dataset.Dataset:
    """Get a cached PyArrow dataset for a Delta table."""
    now = time.time()

    # Check if cached and not expired
    if table_key in _dataset_cache:
        cache_age = now - _dataset_cache_time.get(table_key, 0)
        if cache_age < _CACHE_TTL_SECONDS:
            logger.debug(f"Using cached dataset for {table_key}")
            return _dataset_cache[table_key]

    # Load fresh dataset
    logger.info(f"Loading Delta table: {table_key}")
    start = time.time()

    table_uri = get_table_uri(table_key)
    storage_options = get_storage_options()
    dt = DeltaTable(table_uri, storage_options=storage_options)
    dataset = dt.to_pyarrow_dataset()

    elapsed = time.time() - start
    logger.info(f"Loaded {table_key} in {elapsed:.2f}s")

    # Cache it
    _dataset_cache[table_key] = dataset
    _dataset_cache_time[table_key] = now

    return dataset


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


def _load_precomputed_climatology_sync(
    station_code: int,
    start_year: int,
    end_year: int,
) -> pd.DataFrame | None:
    """Sync helper for loading pre-computed climatology stats."""
    import pyarrow.compute as pc

    try:
        dataset = get_cached_dataset("historical/climatology_stats")

        filter_expr = (
            (pc.field("station_code") == station_code)
            & (pc.field("ref_start_year") == start_year)
            & (pc.field("ref_end_year") == end_year)
        )

        table = dataset.to_table(filter=filter_expr)
        return table.to_pandas()

    except Exception as e:
        logger.warning(f"Pre-computed climatology not available: {e}")
        return None


async def load_precomputed_climatology(
    station_code: int,
    start_year: int,
    end_year: int,
) -> pd.DataFrame | None:
    """Load pre-computed climatology stats from Delta Lake."""
    return await asyncio.to_thread(
        _load_precomputed_climatology_sync, station_code, start_year, end_year
    )


def _load_observations_df_sync(
    station_code: int,
    start_year: int,
    end_year: int,
    column: str,
) -> pd.DataFrame:
    """Sync helper for loading observations."""
    import pyarrow.compute as pc

    dataset = get_cached_dataset("historical/observations")

    filter_expr = (
        (pc.field(STATION_CODE_COLUMN) == station_code)
        & (pc.field("year") >= start_year)
        & (pc.field("year") <= end_year)
    )

    table = dataset.to_table(
        columns=[DATE_COLUMN, column],
        filter=filter_expr,
    )

    df = table.to_pandas()
    df = df.rename(columns={DATE_COLUMN: "weather_date"})
    return df


async def load_observations_df(
    station_code: int,
    start_year: int,
    end_year: int,
    column: str,
) -> pd.DataFrame:
    """Load observations from Delta Lake for the specified station and year range."""
    try:
        return await asyncio.to_thread(
            _load_observations_df_sync, station_code, start_year, end_year, column
        )
    except Exception as e:
        logger.error(f"Error loading observations from Delta Lake: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading observations: {str(e)}")


# Cache for station info - stations rarely change
_station_cache: dict[int, StationInfo] = {}


def _get_station_info_sync(station_code: int) -> StationInfo:
    """Sync helper for loading station info."""
    import pyarrow.compute as pc

    dataset = get_cached_dataset("historical/stations")

    filter_expr = pc.field("STATION_CODE") == station_code
    table = dataset.to_table(
        columns=["STATION_CODE", "STATION_NAME", "ELEVATION_M"],
        filter=filter_expr,
    )
    df = table.to_pandas()

    if len(df) == 0:
        return StationInfo(
            code=station_code,
            name=f"Station {station_code}",
            elevation=None,
        )

    row = df.iloc[0]
    name = row.get("STATION_NAME", f"Station {station_code}")
    if pd.isna(name):
        name = f"Station {station_code}"
    elevation = int(row["ELEVATION_M"]) if pd.notna(row.get("ELEVATION_M")) else None

    return StationInfo(
        code=station_code,
        name=name,
        elevation=elevation,
    )


async def get_station_info(station_code: int) -> StationInfo:
    """Get station information from Delta Lake with caching."""
    # Check cache first
    if station_code in _station_cache:
        return _station_cache[station_code]

    try:
        result = await asyncio.to_thread(_get_station_info_sync, station_code)
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
    df: pd.DataFrame,
    column: str,
    aggregation: AggregationPeriod,
) -> list[ClimatologyDataPoint]:
    """Compute climatology statistics from observations DataFrame."""
    if len(df) == 0:
        return []

    df = df.copy()
    df["weather_date"] = pd.to_datetime(df["weather_date"])

    # Add period column based on aggregation type
    if aggregation == AggregationPeriod.DAILY:
        df["period"] = df["weather_date"].dt.dayofyear
        period_range = range(1, 367)  # Days 1-366
    else:
        df["period"] = df["weather_date"].dt.month
        period_range = range(1, 13)  # Months 1-12

    # Group by period and compute all statistics at once
    def compute_stats(group: pd.Series) -> pd.Series:
        valid = group.dropna()
        if len(valid) == 0:
            return pd.Series(
                {"mean": None, "p10": None, "p25": None, "p50": None, "p75": None, "p90": None}
            )
        values = valid.to_numpy()
        return pd.Series(
            {
                "mean": float(np.mean(values)),
                "p10": float(np.percentile(values, 10)),
                "p25": float(np.percentile(values, 25)),
                "p50": float(np.percentile(values, 50)),
                "p75": float(np.percentile(values, 75)),
                "p90": float(np.percentile(values, 90)),
            }
        )

    stats_df = df.groupby("period")[column].apply(compute_stats).unstack()

    # Build result list, filling in missing periods with nulls
    climatology_data = []
    for period in period_range:
        if period in stats_df.index:
            row = stats_df.loc[period]
            climatology_data.append(
                ClimatologyDataPoint(
                    period=period,
                    mean=row["mean"],
                    p10=row["p10"],
                    p25=row["p25"],
                    p50=row["p50"],
                    p75=row["p75"],
                    p90=row["p90"],
                )
            )
        else:
            climatology_data.append(
                ClimatologyDataPoint(
                    period=period,
                    mean=None,
                    p10=None,
                    p25=None,
                    p50=None,
                    p75=None,
                    p90=None,
                )
            )

    return climatology_data


def extract_current_year_data(
    df: pd.DataFrame,
    column: str,
    year: int,
    aggregation: AggregationPeriod,
) -> list[CurrentYearDataPoint]:
    """Extract current year data from observations DataFrame."""
    if len(df) == 0:
        return []

    df = df.copy()
    df["weather_date"] = pd.to_datetime(df["weather_date"])
    df["year"] = df["weather_date"].dt.year

    # Filter to the comparison year
    year_df = df[df["year"] == year].copy()

    if len(year_df) == 0:
        return []

    # Add period column
    if aggregation == AggregationPeriod.DAILY:
        year_df["period"] = year_df["weather_date"].dt.dayofyear
    else:
        year_df["period"] = year_df["weather_date"].dt.month

    # Aggregate by period (average of hourly values)
    aggregated = (
        year_df.groupby("period")
        .agg(
            {
                column: "mean",
                "weather_date": "first",
            }
        )
        .reset_index()
    )

    # Vectorized conversion - avoid iterrows()
    aggregated["date_str"] = aggregated["weather_date"].dt.strftime("%Y-%m-%d")

    return [
        CurrentYearDataPoint(
            period=int(period),
            value=float(value) if pd.notna(value) else None,
            date=date_str,
        )
        for period, value, date_str in zip(
            aggregated["period"], aggregated[column], aggregated["date_str"]
        )
    ]


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
    import pyarrow.compute as pc
    from deltalake import write_deltalake

    obs_uri = get_table_uri("historical/observations")
    stats_uri = get_table_uri("historical/climatology_stats")
    storage_options = get_storage_options()

    try:
        dt = DeltaTable(obs_uri, storage_options=storage_options)
        dataset = dt.to_pyarrow_dataset()

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
        table = dataset.to_table(columns=columns, filter=filter_expr)
        df = table.to_pandas()
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
        comparison_task = load_observations_df(
            station_code=request.station_code,
            start_year=comparison_year,
            end_year=comparison_year,
            column=column,
        )

    # Wait for all parallel tasks
    if comparison_task:
        precomputed, station_info, comparison_df = await asyncio.gather(
            precomputed_task, station_task, comparison_task
        )
    else:
        precomputed, station_info = await asyncio.gather(precomputed_task, station_task)
        comparison_df = None

    # Process precomputed stats or fall back to computing on-the-fly
    if precomputed is not None and len(precomputed) > 0:
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

        # Vectorized conversion - avoid iterrows()
        def safe_float(val: object) -> float | None:
            if val is None or (isinstance(val, float) and np.isnan(val)):
                return None
            return float(val)  # type: ignore[arg-type]

        def get_column(df: pd.DataFrame, col: str) -> list:
            return df[col].tolist() if col in df.columns else [None] * len(df)

        climatology = [
            ClimatologyDataPoint(
                period=int(day),
                mean=safe_float(mean),
                p10=safe_float(p10),
                p25=safe_float(p25),
                p50=safe_float(p50),
                p75=safe_float(p75),
                p90=safe_float(p90),
            )
            for day, mean, p10, p25, p50, p75, p90 in zip(
                precomputed["day_of_year"].tolist(),
                get_column(precomputed, f"{prefix}_mean"),
                get_column(precomputed, f"{prefix}_p10"),
                get_column(precomputed, f"{prefix}_p25"),
                get_column(precomputed, f"{prefix}_p50"),
                get_column(precomputed, f"{prefix}_p75"),
                get_column(precomputed, f"{prefix}_p90"),
            )
        ]
    else:
        logger.info("Pre-computed stats not available, computing on-the-fly (slow)")
        # Fall back to computing on-the-fly
        start_year = request.reference_period.start_year
        end_year = request.reference_period.end_year

        if comparison_year:
            start_year = min(start_year, comparison_year)
            end_year = max(end_year, comparison_year)

        df = await load_observations_df(
            station_code=request.station_code,
            start_year=start_year,
            end_year=end_year,
            column=column,
        )

        df_with_year = df.copy()
        df_with_year["weather_date"] = pd.to_datetime(df_with_year["weather_date"])
        df_with_year["year"] = df_with_year["weather_date"].dt.year

        year_mask = (df_with_year["year"] >= request.reference_period.start_year) & (
            df_with_year["year"] <= request.reference_period.end_year
        )
        ref_df: pd.DataFrame = df_with_year.loc[year_mask, ["weather_date", column]].copy()

        climatology = compute_climatology(ref_df, column, request.aggregation)

    # Extract comparison year data if loaded
    current_year_data: list[CurrentYearDataPoint] = []
    if comparison_year and comparison_df is not None:
        current_year_data = extract_current_year_data(
            comparison_df, column, comparison_year, request.aggregation
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
