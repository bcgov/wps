"""Pydantic schemas for climatology endpoints."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class WeatherVariable(str, Enum):
    """Supported weather variables for climatology analysis."""

    HOURLY_TEMPERATURE = "HOURLY_TEMPERATURE"
    HOURLY_RELATIVE_HUMIDITY = "HOURLY_RELATIVE_HUMIDITY"
    HOURLY_WIND_SPEED = "HOURLY_WIND_SPEED"
    HOURLY_PRECIPITATION = "HOURLY_PRECIPITATION"
    HOURLY_FINE_FUEL_MOISTURE_CODE = "HOURLY_FINE_FUEL_MOISTURE_CODE"
    HOURLY_INITIAL_SPREAD_INDEX = "HOURLY_INITIAL_SPREAD_INDEX"
    HOURLY_FIRE_WEATHER_INDEX = "HOURLY_FIRE_WEATHER_INDEX"


class AggregationPeriod(str, Enum):
    """Time period for aggregating climatology data."""

    DAILY = "daily"
    MONTHLY = "monthly"


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


class ComparisonYearDataPoint(BaseModel):
    """A data point for the comparison year."""

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
    comparison_year_data: list[ComparisonYearDataPoint] = Field(default_factory=list)
    station: StationInfo
    variable: WeatherVariable
    aggregation: AggregationPeriod
    reference_period: ReferencePeriod
    comparison_year: Optional[int] = None
