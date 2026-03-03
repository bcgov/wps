import argparse
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import numpy as np
from aiohttp import ClientSession
from wps_sfms.interpolation.source import (
    DEW_POINT_LAPSE_RATE,
    LAPSE_RATE,
    StationActualSource,
    StationDewPointSource,
    StationTemperatureSource,
    StationWindVectorSource,
)
from wps_shared.geospatial.spatial_interpolation import idw_interpolation
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_wf1.wfwx_api import WfwxApi

from wps_tools.sfms_histogram import create_sfms_histogram
from wps_tools.sfms_scatterplot import create_sfms_scatterplot


MIN_WIND_SPEED_FOR_DIRECTION_KMH = 1.0


def leave_one_out_idw(lats: np.ndarray, lons: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Leave-one-out IDW interpolation for station arrays."""
    n = len(lats)
    mask = np.ones(n, dtype=bool)
    interpolated_values = np.full(n, np.nan, dtype=np.float32)
    if n < 2:
        return interpolated_values

    for i in range(n):
        mask[i] = False
        interpolated_values[i] = idw_interpolation(
            lats[i], lons[i], lats[mask], lons[mask], values[mask]
        )
        mask[i] = True

    return interpolated_values


def interpolate_temp(sfms_actuals: List[SFMSDailyActual]):
    temp_source = StationTemperatureSource(sfms_actuals)
    lats, lons, elevs, values = temp_source.get_station_arrays(only_valid=True)
    sea = StationTemperatureSource.compute_sea_level_values(values, elevs, LAPSE_RATE)
    assert len(lats) == len(lons) == len(elevs) == len(values) == len(sea)
    sea_interpolated = leave_one_out_idw(lats, lons, sea)

    interpolated_values = StationTemperatureSource.compute_adjusted_values(
        sea_interpolated, elevs, LAPSE_RATE
    )

    return (elevs, values, interpolated_values)


def interpolate_dewpoint_temp(sfms_actuals: List[SFMSDailyActual]):
    dewpoint_source = StationDewPointSource(sfms_actuals)
    lats, lons, elevs, values = dewpoint_source.get_station_arrays(only_valid=True)
    sea = StationDewPointSource.compute_sea_level_values(values, elevs, DEW_POINT_LAPSE_RATE)
    assert len(lats) == len(lons) == len(elevs) == len(values) == len(sea)
    sea_interpolated = leave_one_out_idw(lats, lons, sea)

    interpolated_values = StationDewPointSource.compute_adjusted_values(
        sea_interpolated, elevs, DEW_POINT_LAPSE_RATE
    )
    return (elevs, values, interpolated_values)


def interpolate_wind_speed(sfms_actuals: List[SFMSDailyActual]):
    valid = [s for s in sfms_actuals if s.wind_speed is not None]
    lats = np.array([s.lat for s in valid], dtype=np.float32)
    lons = np.array([s.lon for s in valid], dtype=np.float32)
    observed_wind_speed = np.array([s.wind_speed for s in valid], dtype=np.float32)
    interpolated_wind_speed = leave_one_out_idw(lats, lons, observed_wind_speed)
    return (observed_wind_speed, interpolated_wind_speed)


def circular_difference_degrees(generated: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Smallest signed angular difference in degrees in [-180, 180)."""
    return (generated - reference + 180.0) % 360.0 - 180.0


def interpolate_wind_direction(sfms_actuals: List[SFMSDailyActual]):
    valid = [s for s in sfms_actuals if s.wind_speed is not None and s.wind_direction is not None]
    lats = np.array([s.lat for s in valid], dtype=np.float32)
    lons = np.array([s.lon for s in valid], dtype=np.float32)
    observed_wind_speed = np.array([s.wind_speed for s in valid], dtype=np.float32)
    observed_wind_direction = np.array([s.wind_direction for s in valid], dtype=np.float32)

    wind_vector_source = StationWindVectorSource(valid)
    _, _, station_u, station_v = wind_vector_source.get_uv_interpolation_data()
    interpolated_u = leave_one_out_idw(lats, lons, station_u)
    interpolated_v = leave_one_out_idw(lats, lons, station_v)

    interpolated_wind_direction = np.zeros(len(interpolated_u), dtype=np.float32)
    eps = np.float32(1e-6)
    zero_v = np.abs(interpolated_v) < eps
    nonzero_v = ~zero_v
    interpolated_wind_direction[nonzero_v] = (
        np.degrees(np.arctan2(interpolated_u[nonzero_v], interpolated_v[nonzero_v])) + 180.0
    )
    zero_u = np.abs(interpolated_u) < eps
    interpolated_wind_direction[zero_v & (interpolated_u < 0.0)] = 90.0
    interpolated_wind_direction[zero_v & (interpolated_u > 0.0)] = 270.0
    interpolated_wind_direction[zero_v & zero_u] = 0.0
    return (
        observed_wind_speed,
        observed_wind_direction,
        interpolated_wind_direction,
    )


async def main(start: datetime, end: datetime, out_dir: Optional[Path]):
    # Assemble the data needed for comparison
    async with ClientSession() as client_session:
        wfwx_api = WfwxApi(client_session)
        num_days = (end - start).days
        initial_dt = start.replace(hour=20, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        for i in range(num_days + 1):
            datetime_to_process = initial_dt + timedelta(days=i)
            sfms_actuals = await wfwx_api.get_sfms_daily_actuals_all_stations(datetime_to_process)
            elevs, observed_temps, interpolated_temps = interpolate_temp(sfms_actuals)
            _, _, interpolated_dewpoint_temps = interpolate_dewpoint_temp(sfms_actuals)

            interpolated_rh_from_observed_temps = StationDewPointSource.compute_rh(
                observed_temps, interpolated_dewpoint_temps
            )

            # Get observed rh values for comparison
            rh_source = StationActualSource("relative_humidity", sfms_actuals)
            _, _, observed_rh = rh_source.get_interpolation_data()
            observed_rh_np = np.array(observed_rh)
            # Weather stations show a rh of 0.0 when no observation is present
            observed_rh_masked = observed_rh_np[observed_rh_np > 0.0]

            # Plot percent difference observed - interpolated temp
            temp_difference = observed_temps - interpolated_temps
            temp_difference_percent = temp_difference / observed_temps * 100
            create_sfms_scatterplot(
                elevs,
                temp_difference_percent,
                "Elevation (m)",
                "% Temp Diff",
                f"Temp Percent Difference Observed/Interpolated vs Elevation - {datetime_to_process.date()}",
                out_dir,
                f"temp_diff_vs_elevation_{datetime_to_process.date()}.png",
                True,
            )
            # Create histogram of temp differences
            create_sfms_histogram(
                temp_difference,
                "Difference: Interpolated - Observed",
                "",
                f"Temp Difference: Observed - Interpolated - {datetime_to_process.date()}",
                f"{out_dir}/temp_diff_histogram_{datetime_to_process.date()}.png",
            )

            # Plot percent difference observed - interpolated rh
            rh_difference = observed_rh_masked - interpolated_rh_from_observed_temps
            rh_difference_percent = rh_difference / observed_rh_masked * 100
            create_sfms_scatterplot(
                elevs,
                rh_difference_percent,
                "Elevation (m)",
                "% RH Diff",
                f"RH Percent Difference Observed/Interpolated vs Elevation - {datetime_to_process.date()}",
                out_dir,
                f"rh_diff_vs_elevation_{datetime_to_process.date()}.png",
                True,
            )
            # Create histogram of rh differences
            create_sfms_histogram(
                rh_difference_percent,
                "Difference: Observed - Interpolated",
                "",
                f"RH Difference: Observed - Interpolated - {datetime_to_process.date()}",
                f"{out_dir}/rh_diff_histogram_{datetime_to_process.date()}.png",
            )

            observed_wind_speed, interpolated_wind_speed = interpolate_wind_speed(sfms_actuals)
            wind_speed_difference = observed_wind_speed - interpolated_wind_speed

            create_sfms_histogram(
                wind_speed_difference,
                "Difference: Observed - Interpolated",
                "",
                f"Wind Speed Difference: Observed - Interpolated - {datetime_to_process.date()}",
                f"{out_dir}/wind_speed_diff_histogram_{datetime_to_process.date()}.png",
            )

            (
                wind_direction_observed_speed,
                observed_wind_direction,
                interpolated_wind_direction,
            ) = interpolate_wind_direction(sfms_actuals)
            wind_direction_difference = circular_difference_degrees(
                observed_wind_direction, interpolated_wind_direction
            )

            wind_direction_mask = (
                np.isfinite(wind_direction_difference)
                & np.isfinite(wind_direction_observed_speed)
                & (wind_direction_observed_speed >= MIN_WIND_SPEED_FOR_DIRECTION_KMH)
            )

            masked_direction_error = wind_direction_difference[wind_direction_mask]

            create_sfms_histogram(
                masked_direction_error,
                "Difference: Observed - Interpolated (deg)",
                "",
                (
                    "Wind Direction Difference: Observed - Interpolated "
                    f"(wind >= {MIN_WIND_SPEED_FOR_DIRECTION_KMH:.1f} km/h) - "
                    f"{datetime_to_process.date()}"
                ),
                f"{out_dir}/wind_direction_diff_histogram_{datetime_to_process.date()}.png",
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Perform leave one out testing of weather param interpolation and plot results for each date in the provided range."
    )
    parser.add_argument(
        "--out_dir",
        help="The location to save the generated scatterplots and histograms.",
    )
    parser.add_argument("--start", help="The start date.")
    parser.add_argument("--end", help="The end date.")

    args = parser.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.end, "%Y-%m-%d")
    out_dir: Optional[Path] = Path(args.out_dir) if args.out_dir is not None else None
    asyncio.run(main(start, end, out_dir))
