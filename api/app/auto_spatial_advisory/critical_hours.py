import asyncio
from collections import defaultdict
from datetime import date, datetime, timedelta
import math
from typing import Dict, List, Tuple, Any
import numpy as np
import os
import sys
from time import perf_counter
import logging
from dataclasses import dataclass
from aiohttp import ClientSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app import configure_logging
from app.auto_spatial_advisory.run_type import RunType
from app.db.crud.auto_spatial_advisory import (
    get_all_sfms_fuel_type_records,
    get_containing_zone,
    get_fuel_type_stats_in_advisory_area,
    get_most_recent_run_parameters,
    get_run_parameters_id,
    save_all_critical_hours,
)
from app.db.database import get_async_write_session_scope
from app.db.models.auto_spatial_advisory import AdvisoryFuelStats, CriticalHours, HfiClassificationThresholdEnum, RunTypeEnum, SFMSFuelType
from app.fire_behaviour import cffdrs
from app.fire_behaviour.fuel_types import FUEL_TYPE_DEFAULTS, FuelTypeEnum
from app.fire_behaviour.prediction import build_hourly_rh_dict, calculate_cfb, get_critical_hours
from app.hourlies import get_hourly_readings_in_time_interval
from app.schemas.fba_calc import CriticalHoursHFI, WindResult
from app.schemas.observations import WeatherStationHourlyReadings
from app.stations import get_stations_asynchronously
from app.utils.geospatial import PointTransformer
from app.utils.time import get_hour_20_from_date, get_julian_date
from app.wildfire_one import wfwx_api
from app.wildfire_one.schema_parsers import WFWXWeatherStation

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CriticalHoursInputs:
    """
    Encapsulates the dailies, yesterday dailies and hourlies for a set of stations required for calculating critical hours.
    Since daily data comes from WF1 as JSON, we treat the values as Any types for now.
    """

    dailies_by_station_id: Dict[str, Any]
    yesterday_dailies_by_station_id: Dict[str, Any]
    hourly_observations_by_station_code: Dict[int, WeatherStationHourlyReadings]


def determine_start_time(times: list[float]) -> float:
    """
    Returns a single start time based on a naive heuristic.

    :param times: A list of potential critical hour start times.
    :return: A single start time.
    """
    if len(times) < 3:
        return min(times)
    return math.floor(np.percentile(times, 25))


def determine_end_time(times: list[float]) -> float:
    """
    Returns a single end time based on a naive heuristic.

    :param times: A list of potential critical hour end times.
    :return: A single end time.
    """
    if len(times) < 3:
        return max(times)
    return math.ceil(np.percentile(times, 75))


def calculate_representative_hours(critical_hours: List[CriticalHoursHFI]):
    """
    Naively determines start and end times from a list of CriticalHours objects.

    :param critical_hours: A list of CriticalHours objects.
    :return: Representative start and end time.
    """
    start_times = []
    end_times = []
    for hours in critical_hours:
        start_times.append(hours.start)
        end_times.append(hours.end)
    start_time = determine_start_time(start_times)
    end_time = determine_end_time(end_times)
    return (start_time, end_time)


async def get_fuel_types_dict(db_session: AsyncSession):
    """
    Gets a dictionary of fuel types keyed by fuel type code.

    :param db_session: An async database session.
    :return: A dictionary of fuel types keyed by fuel type code.
    """
    sfms_fuel_types = await get_all_sfms_fuel_type_records(db_session)
    fuel_types_dict = defaultdict()
    for fuel_type in sfms_fuel_types:
        fuel_types_dict[fuel_type[0].fuel_type_code] = fuel_type[0].id
    return fuel_types_dict


async def save_critical_hours(db_session: AsyncSession, zone_unit_id: int, critical_hours_by_fuel_type: dict, run_parameters_id: int):
    """
    Saves CriticalHours records to the API database.

    :param db_session: An async database session.
    :param zone_id: A zone unit id.
    :param critical_hours_by_fuel_type: A dictionary of critical hours for the specified zone unit keyed by fuel type code.
    :param run_parameters_id: The RunParameters id associated with these critical hours (ie an SFMS run).
    """
    sfms_fuel_types_dict = await get_fuel_types_dict(db_session)
    critical_hours_to_save: list[CriticalHours] = []
    for fuel_type, critical_hours in critical_hours_by_fuel_type.items():
        start_time, end_time = calculate_representative_hours(critical_hours)
        critical_hours_record = CriticalHours(
            advisory_shape_id=zone_unit_id,
            threshold=HfiClassificationThresholdEnum.ADVISORY.value,
            run_parameters=run_parameters_id,
            fuel_type=sfms_fuel_types_dict[fuel_type],
            start_hour=start_time,
            end_hour=end_time,
        )
        critical_hours_to_save.append(critical_hours_record)
    await save_all_critical_hours(db_session, critical_hours_to_save)


def calculate_wind_speed_result(yesterday: dict, raw_daily: dict) -> WindResult:
    """
    Calculates new FWIs based on observed and forecast daily data from WF1.

    :param yesterday: Weather parameter observations and FWIs from yesterday.
    :param raw_daily: Forecasted weather parameters from WF1.
    :return: A WindResult object with calculated FWIs.
    """
    # extract variables from wf1 that we need to calculate the fire behaviour advisory.
    bui = cffdrs.bui_calc(raw_daily.get("duffMoistureCode", None), raw_daily.get("droughtCode", None))
    temperature = raw_daily.get("temperature", None)
    relative_humidity = raw_daily.get("relativeHumidity", None)
    precipitation = raw_daily.get("precipitation", None)

    wind_speed = raw_daily.get("windSpeed", None)
    status = raw_daily.get("recordType").get("id")

    ffmc = cffdrs.fine_fuel_moisture_code(yesterday.get("fineFuelMoistureCode", None), temperature, relative_humidity, precipitation, wind_speed)
    isi = cffdrs.initial_spread_index(ffmc, wind_speed)
    fwi = cffdrs.fire_weather_index(isi, bui)
    return WindResult(ffmc=ffmc, isi=isi, bui=bui, wind_speed=wind_speed, fwi=fwi, status=status)


def calculate_critical_hours_for_station_by_fuel_type(
    wfwx_station: WFWXWeatherStation,
    critical_hours_inputs: CriticalHoursInputs,
    fuel_type: FuelTypeEnum,
    for_date: datetime,
):
    """
    Calculate the critical hours for a fuel type - station pair.

    :param wfwx_station: The WFWXWeatherStation.
    :param critical_hours_inputs: Dailies, yesterday dailies, hourlies required to calculate critical hours
    :param fuel_type: The fuel type of interest.
    :param for_date: The date critical hours are being calculated for.
    :return: The critical hours for the station and fuel type.
    """
    raw_daily = critical_hours_inputs.dailies_by_station_id[wfwx_station.wfwx_id]
    raw_observations = critical_hours_inputs.hourly_observations_by_station_code[wfwx_station.code]
    yesterday = critical_hours_inputs.yesterday_dailies_by_station_id[wfwx_station.wfwx_id]
    last_observed_morning_rh_values = build_hourly_rh_dict(raw_observations.values)

    wind_result = calculate_wind_speed_result(yesterday, raw_daily)
    bui = wind_result.bui
    ffmc = wind_result.ffmc
    isi = wind_result.isi
    fuel_type_info = FUEL_TYPE_DEFAULTS[fuel_type]
    percentage_conifer = fuel_type_info.get("PC", None)
    percentage_dead_balsam_fir = fuel_type_info.get("PDF", None)
    crown_base_height = fuel_type_info.get("CBH", None)
    cfl = fuel_type_info.get("CFL", None)
    grass_cure = yesterday.get("grasslandCuring", None)
    wind_speed = wind_result.wind_speed
    yesterday_ffmc = yesterday.get("fineFuelMoistureCode", None)
    julian_date = get_julian_date(for_date)
    fmc = cffdrs.foliar_moisture_content(int(wfwx_station.lat), int(wfwx_station.long), wfwx_station.elevation, julian_date)
    sfc = cffdrs.surface_fuel_consumption(fuel_type, bui, ffmc, percentage_conifer)
    ros = cffdrs.rate_of_spread(
        fuel_type,
        isi=isi,
        bui=bui,
        fmc=fmc,
        sfc=sfc,
        pc=percentage_conifer,
        cc=grass_cure,
        pdf=percentage_dead_balsam_fir,
        cbh=crown_base_height,
    )
    cfb = calculate_cfb(fuel_type, fmc, sfc, ros, crown_base_height)

    critical_hours = get_critical_hours(
        4000,
        fuel_type,
        percentage_conifer,
        percentage_dead_balsam_fir,
        bui,
        grass_cure,
        crown_base_height,
        ffmc,
        fmc,
        cfb,
        cfl,
        wind_speed,
        yesterday_ffmc,
        last_observed_morning_rh_values,
    )

    return critical_hours


def calculate_critical_hours_by_fuel_type(wfwx_stations: List[WFWXWeatherStation], critical_hours_inputs: CriticalHoursInputs, fuel_types_by_area, for_date):
    """
    Calculates the critical hours for each fuel type for all stations in a fire zone unit.

    :param wfwx_stations: A list of WFWXWeatherStations in a single fire zone unit.
    :param dailies_by_station_id: Today's weather observations (or forecasts) keyed by station guid.
    :param yesterday_dailies_by_station_id: Yesterday's weather observations and FWIs keyed by station guid.
    :param hourly_observations_by_station_id: Hourly observations from the past 4 days keyed by station guid.
    :param fuel_types_by_area: The fuel types and their areas exceeding a high HFI threshold.
    :param for_date: The date critical hours are being calculated for.
    :return: A dictionary of lists of critical hours keyed by fuel type code.
    """
    critical_hours_by_fuel_type = defaultdict(list)
    for wfwx_station in wfwx_stations:
        if check_station_valid(wfwx_station, critical_hours_inputs):
            for fuel_type_key in fuel_types_by_area.keys():
                fuel_type_enum = FuelTypeEnum(fuel_type_key.replace("-", ""))
                try:
                    # Placing critical hours calculation in a try/except block as failure to calculate critical hours for a single station/fuel type pair
                    # shouldn't prevent us from continuing with other stations and fuel types.

                    critical_hours = calculate_critical_hours_for_station_by_fuel_type(wfwx_station, critical_hours_inputs, fuel_type_enum, for_date)
                    if critical_hours is not None and critical_hours.start is not None and critical_hours.end is not None:
                        logger.info(f"Calculated critical hours for fuel type key: {fuel_type_key}, start: {critical_hours.start}, end: {critical_hours.end}")
                        critical_hours_by_fuel_type[fuel_type_key].append(critical_hours)
                except Exception as exc:
                    logger.warning(f"An error occurred when calculating critical hours for station code: {wfwx_station.code} and fuel type: {fuel_type_key}: {exc} ")
    return critical_hours_by_fuel_type


def check_station_valid(wfwx_station: WFWXWeatherStation, critical_hours_inputs: CriticalHoursInputs) -> bool:
    """
    Checks if there is sufficient information to calculate critical hours for the specified station.

    :param wfwx_station: The station of interest.
    :param yesterdays: Yesterday's station data based on observations and FWI calculations.
    :param hourlies: Hourly observations from yesterday.
    :return: True if the station can be used for critical hours calculations, otherwise false.
    """
    if wfwx_station.wfwx_id not in critical_hours_inputs.dailies_by_station_id or wfwx_station.code not in critical_hours_inputs.hourly_observations_by_station_code:
        logger.info(f"Station with code: ${wfwx_station.code} is missing dailies or hourlies")
        return False
    daily = critical_hours_inputs.dailies_by_station_id[wfwx_station.wfwx_id]
    if daily["duffMoistureCode"] is None or daily["droughtCode"] is None or daily["fineFuelMoistureCode"] is None:
        logger.info(f"Station with code: ${wfwx_station.code} is missing DMC, DC or FFMC")
        return False
    return True


async def get_hourly_observations(station_codes: List[int], start_time: datetime, end_time: datetime):
    """
    Gets hourly weather observations from WF1.

    :param station_codes: A list of weather station codes.
    :param start_time: The start time of interest.
    :param end_time: The end time of interest.
    :return: Hourly weather observations from WF1 for all specified station codes.
    """
    hourly_observations = await get_hourly_readings_in_time_interval(station_codes, start_time, end_time)
    # also turn hourly obs data into a dict indexed by station id
    hourly_observations_by_station_code = {raw_hourly.station.code: raw_hourly for raw_hourly in hourly_observations}
    return hourly_observations_by_station_code


async def get_dailies_by_station_id(client_session: ClientSession, header: dict, wfwx_stations: List[WFWXWeatherStation], time_of_interest: datetime):
    """
    Gets daily observations or forecasts from WF1.

    :param client_session: A client session for making web requests.
    :param header: An authorization header for making requests to WF1.
    :param wfwx_stations: A list of WFWXWeatherStations.
    :param time_of_interest: The time of interest (typically at 20:00 UTC).
    :return: Daily observations or forecasts from WF1.
    """
    dailies = await wfwx_api.get_dailies_generator(client_session, header, wfwx_stations, time_of_interest, time_of_interest)
    # turn it into a dictionary so we can easily get at data using a station id
    dailies_by_station_id = {raw_daily.get("stationId"): raw_daily async for raw_daily in dailies}
    return dailies_by_station_id


def get_fuel_types_by_area(advisory_fuel_stats: List[Tuple[AdvisoryFuelStats, SFMSFuelType]]) -> Dict[str, float]:
    """
    Aggregates high HFI area for zone units.

    :param advisory_fuel_stats: A list of fire zone units that includes area exceeding 4K kW/m and 10K kW/m.
    :return: Fuel types and the total area exceeding an HFI threshold of 4K kW/m.
    """
    fuel_types_by_area = {}
    for row in advisory_fuel_stats:
        advisory_fuel_stat = row[0]
        sfms_fuel_type = row[1]
        key = sfms_fuel_type.fuel_type_code
        if key == "Non-fuel":
            continue
        if key in fuel_types_by_area:
            fuel_types_by_area[key] += advisory_fuel_stat.area
        else:
            fuel_types_by_area[key] = advisory_fuel_stat.area
    return fuel_types_by_area


async def get_inputs_for_critical_hours(for_date: date, header: dict, wfwx_stations: List[WFWXWeatherStation]) -> CriticalHoursInputs:
    """
    Retrieves the inputs required for computing critical hours based on the station list and for date

    :param for_date: date of interest for looking up dailies and hourlies
    :param header: auth header for requesting data from WF1
    :param wfwx_stations: list of stations to compute critical hours for
    :return: critical hours inputs
    """
    unique_station_codes = list(set(station.code for station in wfwx_stations))
    time_of_interest = get_hour_20_from_date(for_date)

    # get the dailies for all the stations
    async with ClientSession() as client_session:
        dailies_by_station_id = await get_dailies_by_station_id(client_session, header, wfwx_stations, time_of_interest)
        # must retrieve the previous day's observed/forecasted FFMC value from WFWX
        prev_day = time_of_interest - timedelta(days=1)
        # get the "daily" data for the station for the previous day
        yesterday_dailies_by_station_id = await get_dailies_by_station_id(client_session, header, wfwx_stations, prev_day)
        # get hourly observation history from our API (used for calculating morning diurnal FFMC)
        hourly_observations_by_station_code = await get_hourly_observations(unique_station_codes, time_of_interest - timedelta(days=4), time_of_interest)

        return CriticalHoursInputs(
            dailies_by_station_id=dailies_by_station_id,
            yesterday_dailies_by_station_id=yesterday_dailies_by_station_id,
            hourly_observations_by_station_code=hourly_observations_by_station_code,
        )


async def calculate_critical_hours_by_zone(db_session: AsyncSession, header: dict, stations_by_zone: Dict[int, List[WFWXWeatherStation]], run_parameters_id: int, for_date: date):
    """
    Calculates critical hours for fire zone units by heuristically determining critical hours for each station in the fire zone unit that are under advisory conditions (>4k HFI).

    :param db_session: An async database session.
    :param header: An authorization header for making requests to WF1.
    :param stations_by_zone: A dictionary of lists of stations in fire zone units keyed by fire zone unit id.
    :param run_parameters_id: The RunParameters object (ie. the SFMS run).
    :param for_date: The date critical hours are being calculated for.
    """
    critical_hours_by_zone_and_fuel_type = defaultdict(str, defaultdict(list))
    for zone_key in stations_by_zone.keys():
        advisory_fuel_stats = await get_fuel_type_stats_in_advisory_area(db_session, zone_key, run_parameters_id)
        fuel_types_by_area = get_fuel_types_by_area(advisory_fuel_stats)
        wfwx_stations = stations_by_zone[zone_key]
        critical_hours_inputs = await get_inputs_for_critical_hours(for_date, header, wfwx_stations)
        critical_hours_by_fuel_type = calculate_critical_hours_by_fuel_type(
            wfwx_stations,
            critical_hours_inputs,
            fuel_types_by_area,
            for_date,
        )

        if len(critical_hours_by_fuel_type) > 0:
            critical_hours_by_zone_and_fuel_type[zone_key] = critical_hours_by_fuel_type

    for zone_id, critical_hours_by_fuel_type in critical_hours_by_zone_and_fuel_type.items():
        await save_critical_hours(db_session, zone_id, critical_hours_by_fuel_type, run_parameters_id)


async def calculate_critical_hours(run_type: RunType, run_datetime: datetime, for_date: date):
    """
    Entry point for calculating critical hours.

    :param run_type: The run type, either forecast or actual.
    :param run_datetime: The date and time of the sfms run.
    :param for_date: The date critical hours are being calculated for.
    """

    logger.info(f"Calculating critical hours for {run_type} run type on run date: {run_datetime}, for date: {for_date}")
    perf_start = perf_counter()

    async with get_async_write_session_scope() as db_session:
        run_parameters_id = await get_run_parameters_id(db_session, RunType(run_type), run_datetime, for_date)
        stmt = select(CriticalHours).where(CriticalHours.run_parameters == run_parameters_id)
        exists = (await db_session.execute(stmt)).scalars().first() is not None

        if exists:
            logger.info("Critical hours already processed.")
            return

        async with ClientSession() as client_session:
            header = await wfwx_api.get_auth_header(client_session)
            all_stations = await get_stations_asynchronously()
            station_codes = list(station.code for station in all_stations)
            stations = await wfwx_api.get_wfwx_stations_from_station_codes(client_session, header, station_codes)
            stations_by_zone: Dict[int, List[WFWXWeatherStation]] = defaultdict(list)
            transformer = PointTransformer(4326, 3005)
            for station in stations:
                (x, y) = transformer.transform_coordinate(station.lat, station.long)
                zone_id = await get_containing_zone(db_session, f"POINT({x} {y})", 3005)
                if zone_id is not None:
                    stations_by_zone[zone_id[0]].append(station)

            await calculate_critical_hours_by_zone(db_session, header, stations_by_zone, run_parameters_id, for_date)

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info(f"delta count before and after calculating critical hours: {delta}")


#### - Helper functions for local testing of critical hours calculations.


async def start_critical_hours():
    async with get_async_write_session_scope() as db_session:
        result = await get_most_recent_run_parameters(db_session, RunTypeEnum.actual, date(2024, 8, 1))
        await calculate_critical_hours(result[0].run_type, result[0].run_datetime, result[0].for_date)


def main():
    """Kicks off asynchronous calculation of critical hours."""
    try:
        logger.debug("Begin calculating critical hours.")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_critical_hours())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error("An error occurred while processing critical hours.", exc_info=exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()