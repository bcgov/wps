import argparse
import asyncio
import sys
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
)
from wps_shared.geospatial.spatial_interpolation import idw_interpolation
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_shared.sfms.raster_addresser import SFMSInterpolatedWeatherParameter
from wps_wf1.wfwx_api import WfwxApi

from wps_tools.sfms_histogram import create_sfms_histogram
from wps_tools.sfms_scatterplot import create_sfms_scatterplot


def interpolate_temp(sfms_actuals: List[SFMSDailyActual]):
    temp_source = StationTemperatureSource(sfms_actuals)
    lats, lons, elevs, values = temp_source.get_station_arrays(only_valid=True)
    sea = StationTemperatureSource.compute_sea_level_values(values, elevs, LAPSE_RATE)
    assert len(lats) == len(lons) == len(elevs) == len(values) == len(sea)
    n = len(lats)
    # Mask used for 'leave one out' analysis
    mask = np.ones(n, dtype=bool)
    sea_interpolated = np.full(n, -sys.float_info.max)

    for i in range(n):
        mask[i] = False
        lat = lats[i]
        lon = lons[i]
        sea_interpolated[i] = idw_interpolation(lat, lon, lats[mask], lons[mask], sea[mask])
        mask[i] = True

    interpolated_values = StationTemperatureSource.compute_adjusted_values(
        sea_interpolated, elevs, LAPSE_RATE
    )

    return (elevs, values, interpolated_values)


def interpolate_dewpoint_temp(sfms_actuals: List[SFMSDailyActual]):
    dewpoint_source = StationDewPointSource(sfms_actuals)
    lats, lons, elevs, values = dewpoint_source.get_station_arrays(only_valid=True)
    sea = StationDewPointSource.compute_sea_level_values(values, elevs, DEW_POINT_LAPSE_RATE)
    assert len(lats) == len(lons) == len(elevs) == len(values) == len(sea)
    n = len(lats)
    mask = np.ones(n, dtype=bool)
    sea_interpolated = np.ones(n, dtype=np.float32)

    for i in range(n):
        mask[i] = False
        lat = lats[i]
        lon = lons[i]
        sea_interpolated[i] = idw_interpolation(lat, lon, lats[mask], lons[mask], sea[mask])
        mask[i] = True

    interpolated_values = StationDewPointSource.compute_adjusted_values(
        sea_interpolated, elevs, DEW_POINT_LAPSE_RATE
    )
    return (elevs, values, interpolated_values)


async def main(start: datetime, end: datetime, out_dir: Path):
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

            interpolated_rh_from_observed_temps = StationDewPointSource.compute_rh(observed_temps, interpolated_dewpoint_temps)

            # Get observed rh values for comparison
            rh_source = StationActualSource(SFMSInterpolatedWeatherParameter.RH)
            _, _, observed_rh = rh_source.get_interpolation_data(sfms_actuals)
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

    out_dir: Optional[Path] = None
    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.end, "%Y-%m-%d")
    out_dir = args.out_dir
    asyncio.run(main(start, end, out_dir))
