"""Climatology Router

Provides endpoints for calculating climate normals and comparing current year data
to historical averages across weather stations.
"""

import logging
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd
from deltalake import DeltaTable
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
    aggregation: AggregationPeriod = Field(default=AggregationPeriod.DAILY, description="Aggregation period")
    reference_period: ReferencePeriod = Field(..., description="Reference period for climate normals")
    comparison_year: Optional[int] = Field(default=None, description="Year to compare against normals")


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
) -> pd.DataFrame | None:
    """Load pre-computed climatology stats from Delta Lake."""
    stats_uri = get_table_uri("historical/climatology_stats")
    storage_options = get_storage_options()

    try:
        dt = DeltaTable(stats_uri, storage_options=storage_options)
        df = dt.to_pandas()

        # Filter by station and reference period
        mask = (
            (df["station_code"] == station_code) &
            (df["ref_start_year"] == start_year) &
            (df["ref_end_year"] == end_year)
        )
        return df[mask].copy()

    except Exception as e:
        logger.warning(f"Pre-computed climatology not available: {e}")
        return None


async def load_observations_df(
    station_code: int,
    start_year: int,
    end_year: int,
    column: str,
) -> pd.DataFrame:
    """Load observations from Delta Lake for the specified station and year range."""
    import pyarrow.compute as pc

    obs_uri = get_table_uri("historical/observations")
    storage_options = get_storage_options()

    try:
        dt = DeltaTable(obs_uri, storage_options=storage_options)
        dataset = dt.to_pyarrow_dataset()

        # Build filter with partition pruning on year + station filter
        filter_expr = (
            (pc.field(STATION_CODE_COLUMN) == station_code) &
            (pc.field("year") >= start_year) &
            (pc.field("year") <= end_year)
        )

        # Query with predicate pushdown
        table = dataset.to_table(
            columns=[DATE_COLUMN, column],
            filter=filter_expr,
        )

        df = table.to_pandas()
        df = df.rename(columns={DATE_COLUMN: "weather_date"})
        return df

    except Exception as e:
        logger.error(f"Error loading observations from Delta Lake: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading observations: {str(e)}")


async def get_station_info(station_code: int) -> StationInfo:
    """Get station information from Delta Lake."""
    table_uri = get_table_uri("historical/stations")
    storage_options = get_storage_options()

    try:
        dt = DeltaTable(table_uri, storage_options=storage_options)
        df = dt.to_pandas()

        # Try different possible column name patterns
        station_code_col = None
        station_name_col = None
        elevation_col = None

        for col in df.columns:
            col_upper = col.upper()
            if "STATION" in col_upper and "CODE" in col_upper:
                station_code_col = col
            elif "STATION" in col_upper and "NAME" in col_upper:
                station_name_col = col
            elif "ELEVATION" in col_upper or "ELEV" in col_upper:
                elevation_col = col

        if station_code_col is None:
            logger.warning(f"Could not find station_code column in stations table. Columns: {df.columns.tolist()}")
            return StationInfo(code=station_code, name=f"Station {station_code}", elevation=None)

        station_df = df[df[station_code_col] == station_code]

        if len(station_df) == 0:
            return StationInfo(
                code=station_code,
                name=f"Station {station_code}",
                elevation=None,
            )

        row = station_df.iloc[0]
        name = row[station_name_col] if station_name_col and pd.notna(row.get(station_name_col)) else f"Station {station_code}"
        elevation = int(row[elevation_col]) if elevation_col and pd.notna(row.get(elevation_col)) else None

        return StationInfo(
            code=int(row[station_code_col]),
            name=name,
            elevation=elevation,
        )

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

    # Group by period and compute statistics
    climatology_data = []

    for period in period_range:
        period_data = df[df["period"] == period]

        if len(period_data) == 0:
            climatology_data.append(ClimatologyDataPoint(
                period=period,
                mean=None,
                p10=None,
                p25=None,
                p50=None,
                p75=None,
                p90=None,
            ))
            continue

        values = period_data[column].to_numpy()
        stats = compute_percentiles(values)

        climatology_data.append(ClimatologyDataPoint(
            period=period,
            **stats,
        ))

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
    aggregated = year_df.groupby("period").agg({
        column: "mean",
        "weather_date": "first",
    }).reset_index()

    current_year_data = []
    for _, row in aggregated.iterrows():
        value = row[column]
        current_year_data.append(CurrentYearDataPoint(
            period=int(row["period"]),
            value=float(value) if pd.notna(value) else None,
            date=row["weather_date"].strftime("%Y-%m-%d"),
        ))

    return current_year_data


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
        filter_expr = (
            (pc.field("year") >= start_year) &
            (pc.field("year") <= end_year)
        )

        # Load filtered data
        columns = [
            STATION_CODE_COLUMN, DATE_COLUMN,
            "HOURLY_TEMPERATURE", "HOURLY_RELATIVE_HUMIDITY", "HOURLY_WIND_SPEED",
            "HOURLY_PRECIPITATION", "HOURLY_FINE_FUEL_MOISTURE_CODE",
            "HOURLY_INITIAL_SPREAD_INDEX", "HOURLY_FIRE_WEATHER_INDEX",
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
        stats_df = df.groupby([STATION_CODE_COLUMN, "day_of_year"]).apply(
            compute_stats, include_groups=False
        ).reset_index()
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


@router.post("/optimize", response_model=dict)
async def optimize_observations_table():
    """
    Trigger Z-order optimization on the observations Delta Lake table.

    This colocates data by STATION_CODE for faster station-based queries.
    Should be run after bulk data updates.

    Note: This operation can take a while for large tables.
    """
    logger.info("/climatology/optimize - Starting Z-order optimization")

    table_uri = get_table_uri("historical/observations")
    storage_options = get_storage_options()

    try:
        dt = DeltaTable(table_uri, storage_options=storage_options)

        # Run Z-order optimization on STATION_CODE
        # This colocates data for the same station together
        metrics = dt.optimize.z_order(columns=[STATION_CODE_COLUMN])

        logger.info(f"/climatology/optimize - Z-order complete: {metrics}")

        return {
            "status": "success",
            "message": f"Z-order optimization complete on {STATION_CODE_COLUMN}",
            "metrics": {
                "files_added": metrics.get("numFilesAdded", 0),
                "files_removed": metrics.get("numFilesRemoved", 0),
                "partitions_optimized": metrics.get("numPartitionsOptimized", 0),
            }
        }
    except Exception as e:
        logger.error(f"Error during Z-order optimization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/compact", response_model=dict)
async def compact_observations_table():
    """
    Compact small files in the observations Delta Lake table.

    This merges small files into larger ones for better read performance.
    Should be run periodically or after many small writes.
    """
    logger.info("/climatology/compact - Starting compaction")

    table_uri = get_table_uri("historical/observations")
    storage_options = get_storage_options()

    try:
        dt = DeltaTable(table_uri, storage_options=storage_options)

        # Run compaction
        metrics = dt.optimize.compact()

        logger.info(f"/climatology/compact - Compaction complete: {metrics}")

        return {
            "status": "success",
            "message": "Compaction complete",
            "metrics": {
                "files_added": metrics.get("numFilesAdded", 0),
                "files_removed": metrics.get("numFilesRemoved", 0),
                "partitions_optimized": metrics.get("numPartitionsOptimized", 0),
            }
        }
    except Exception as e:
        logger.error(f"Error during compaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Compaction failed: {str(e)}")


@router.post("/", response_model=ClimatologyResponse)
async def get_climatology(request: ClimatologyRequest):
    """
    Get climatology data for a weather station.

    Returns percentile bands (p10, p25, p50, p75, p90) and mean values computed
    from the reference period, along with the current/comparison year data overlay.

    Uses pre-computed stats if available (much faster), otherwise computes on-the-fly.
    """
    logger.info(f"/climatology/ - station: {request.station_code}, variable: {request.variable.value}")

    # Validate reference period
    if request.reference_period.start_year > request.reference_period.end_year:
        raise HTTPException(
            status_code=400,
            detail="Reference period start_year must be less than or equal to end_year"
        )

    column = VARIABLE_COLUMN_MAP[request.variable]
    comparison_year = request.comparison_year

    # Try to use pre-computed climatology stats (fast path)
    precomputed = await load_precomputed_climatology(
        station_code=request.station_code,
        start_year=request.reference_period.start_year,
        end_year=request.reference_period.end_year,
    )

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

        climatology = []
        for _, row in precomputed.iterrows():
            climatology.append(ClimatologyDataPoint(
                period=int(row["day_of_year"]),
                mean=float(row[f"{prefix}_mean"]) if pd.notna(row.get(f"{prefix}_mean")) else None,
                p10=float(row[f"{prefix}_p10"]) if pd.notna(row.get(f"{prefix}_p10")) else None,
                p25=float(row[f"{prefix}_p25"]) if pd.notna(row.get(f"{prefix}_p25")) else None,
                p50=float(row[f"{prefix}_p50"]) if pd.notna(row.get(f"{prefix}_p50")) else None,
                p75=float(row[f"{prefix}_p75"]) if pd.notna(row.get(f"{prefix}_p75")) else None,
                p90=float(row[f"{prefix}_p90"]) if pd.notna(row.get(f"{prefix}_p90")) else None,
            ))
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

        ref_df = df_with_year[
            (df_with_year["year"] >= request.reference_period.start_year) &
            (df_with_year["year"] <= request.reference_period.end_year)
        ][["weather_date", column]].copy()

        climatology = compute_climatology(ref_df, column, request.aggregation)

    # Extract comparison year data if specified (always needs raw data)
    current_year_data = []
    if comparison_year:
        df = await load_observations_df(
            station_code=request.station_code,
            start_year=comparison_year,
            end_year=comparison_year,
            column=column,
        )
        current_year_data = extract_current_year_data(df, column, comparison_year, request.aggregation)

    # Get station info
    station_info = await get_station_info(request.station_code)

    return ClimatologyResponse(
        climatology=climatology,
        current_year=current_year_data,
        station=station_info,
        variable=request.variable,
        aggregation=request.aggregation,
        reference_period=request.reference_period,
        comparison_year=comparison_year,
    )
