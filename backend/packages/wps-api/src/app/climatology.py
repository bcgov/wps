"""Climatology data access and computation functions."""

from __future__ import annotations

import logging

import pyarrow as pa
import pyarrow.compute as pc

from wps_shared.schemas.climatology import (
    AggregationPeriod,
    ClimatologyDataPoint,
    ComparisonYearDataPoint,
    StationInfo,
)
from wps_shared.utils.delta import DeltaTableWrapper

logger = logging.getLogger(__name__)

DATE_COLUMN = "DATE_TIME"

# Cache for station info - stations rarely change
_station_cache: dict[int, StationInfo] = {}


async def get_station_info(station_code: int) -> StationInfo:
    """Get station information from Delta Lake with caching."""
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

        name_val = table.column("STATION_NAME")[0].as_py()
        elev_val = table.column("ELEVATION_M")[0].as_py()

        result = StationInfo(
            code=station_code,
            name=name_val if name_val is not None else f"Station {station_code}",
            elevation=int(elev_val) if elev_val is not None else None,
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

    timestamps = table.column(DATE_COLUMN)
    if aggregation == AggregationPeriod.DAILY:
        period_arr = pc.day_of_year(timestamps)
        period_range = range(1, 367)
    else:
        period_arr = pc.month(timestamps)
        period_range = range(1, 13)

    table = table.append_column("period", period_arr)
    values_col = table.column(column)

    stats_by_period: dict[int, dict[str, float | None]] = {}

    for period in period_range:
        mask = pc.equal(table.column("period"), period)
        period_values = pc.filter(values_col, mask)
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


def get_comparison_year_data(
    table: pa.Table,
    column: str,
    aggregation: AggregationPeriod,
) -> list[ComparisonYearDataPoint]:
    """Extract current year data from observations using PyArrow."""
    if table.num_rows == 0:
        return []

    timestamps = table.column(DATE_COLUMN)
    values_col = table.column(column)

    if aggregation == AggregationPeriod.DAILY:
        period_arr = pc.day_of_year(timestamps)
    else:
        period_arr = pc.month(timestamps)

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

        valid_values = pc.drop_null(period_values)
        mean_val = pc.mean(valid_values).as_py() if len(valid_values) > 0 else None

        first_ts = period_timestamps[0].as_py()
        date_str = first_ts.strftime("%Y-%m-%d") if first_ts else ""

        results.append(
            ComparisonYearDataPoint(
                period=int(period),
                value=float(mean_val) if mean_val is not None else None,
                date=date_str,
            )
        )

    return results
