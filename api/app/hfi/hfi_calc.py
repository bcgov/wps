""" HFI calculation logic """

import math
import logging
from time import perf_counter
from typing import Mapping, Optional, List, AsyncGenerator
from datetime import date, timedelta
from statistics import mean
from aiohttp.client import ClientSession
import app
from app.db.database import get_read_session_scope
from app.schemas.hfi_calc import (DailyResult, DateRange,
                                  FireStartRange, HFIResultRequest,
                                  PlanningAreaResult,
                                  StationDaily,
                                  ValidatedStationDaily,
                                  required_daily_fields,
                                  lowest_fire_starts)
from app.schemas.hfi_calc import (WeatherStationProperties,
                                  FuelType, FireCentre, PlanningArea, WeatherStation)
from app.utils.time import get_hour_20_from_date
from app.wildfire_one.wfwx_api import (get_auth_header, get_stations_by_codes,
                                       get_wfwx_stations_from_station_codes,
                                       get_raw_dailies_in_range_generator)
from app.wildfire_one.schema_parsers import generate_station_daily
from app.db.crud.hfi_calc import get_fire_centre_stations, get_fire_weather_stations

logger = logging.getLogger(__name__)


def get_prep_day_dailies(dailies_date: date, area_dailies: List[StationDaily]) -> List[StationDaily]:
    """ Return all the dailies (that's noon, or 20 hours UTC) for a given date """
    dailies_date_time = get_hour_20_from_date(dailies_date)
    return list(filter(lambda daily: (daily.date == dailies_date_time), area_dailies))


async def station_daily_generator(raw_daily_generator,
                                  wfwx_stations,
                                  station_fuel_type_map) -> AsyncGenerator[StationDaily, None]:
    """ Generator that yields the daily data for each station.

    We give this function all the puzzle pieces. The raw_daily_generator (reading dailies from
    wfwx and giving us dictionaries) + wfwx_stations (from wfwx) + station_fuel_type_map (from our db).

    The puzzle pieces are mangled together, and the generator then yields a StationDaily object."""
    station_lookup = {station.wfwx_id: station for station in wfwx_stations}
    fuel_type = None
    cumulative = 0
    async for raw_daily in raw_daily_generator:
        start = perf_counter()
        wfwx_station = station_lookup.get(raw_daily.get('stationId'))
        fuel_type = station_fuel_type_map.get(wfwx_station.code)
        result = generate_station_daily(raw_daily, wfwx_station, fuel_type)
        delta = perf_counter() - start
        cumulative = cumulative + delta
        yield result
    # NOTE: Keeping track of the cumulative time here is informative for optimizing code.
    # Calling out to the CFFDRS R library takes a lot of time. Especially if the R engine is starting up.
    logger.info('station_daily_generator cumulative time %f', cumulative)


async def hydrate_fire_centres():
    """Get detailed fire_centres from db and WFWX"""

    # pylint: disable=too-many-locals
    with app.db.database.get_read_session_scope() as session:
        # Fetch all fire weather stations from the database.
        station_query = get_fire_weather_stations(session)
        # Prepare a dictionary for storing station info in.
        station_info_dict = {}
        # Prepare empty data structures to be used in HFIWeatherStationsResponse
        fire_centres_list = []
        planning_areas_dict = {}
        fire_centres_dict = {}

        # Iterate through all the database records, collecting all the data we need.
        for (station_record, fuel_type_record, planning_area_record, fire_centre_record) in station_query:
            station_info_dict[station_record.station_code] = {
                'fuel_type': FuelType(
                    abbrev=fuel_type_record.abbrev,
                    fuel_type_code=fuel_type_record.fuel_type_code,
                    description=fuel_type_record.description,
                    percentage_conifer=fuel_type_record.percentage_conifer,
                    percentage_dead_fir=fuel_type_record.percentage_dead_fir),
                # pylint: disable=line-too-long
                'order_of_appearance_in_planning_area_list': station_record.order_of_appearance_in_planning_area_list,
                'planning_area': planning_area_record,
                'fire_centre': fire_centre_record
            }

            if fire_centres_dict.get(fire_centre_record.id) is None:
                fire_centres_dict[fire_centre_record.id] = {
                    'fire_centre_record': fire_centre_record,
                    'planning_area_records': [planning_area_record],
                    'planning_area_objects': []
                }
            else:
                fire_centres_dict.get(fire_centre_record.id)[
                    'planning_area_records'].append(planning_area_record)
                fire_centres_dict[fire_centre_record.id]['planning_area_records'] = list(
                    set(fire_centres_dict.get(fire_centre_record.id).get('planning_area_records')))

            if planning_areas_dict.get(planning_area_record.id) is None:
                planning_areas_dict[planning_area_record.id] = {
                    'planning_area_record': planning_area_record,
                    'order_of_appearance_in_list': planning_area_record.order_of_appearance_in_list,
                    'station_codes': [station_record.station_code],
                    'station_objects': []
                }
            else:
                planning_areas_dict[planning_area_record.id]['station_codes'].append(
                    station_record.station_code)

        # We're still missing some data that we need from wfwx, so give it the list of stations
        wfwx_stations_data = await get_stations_by_codes(list(station_info_dict.keys()))
        # Iterate through all the stations from wildfire one.

        for wfwx_station in wfwx_stations_data:
            station_info = station_info_dict[wfwx_station.code]
            # Combine everything.
            station_properties = WeatherStationProperties(
                name=wfwx_station.name,
                fuel_type=station_info['fuel_type'],
                elevation=wfwx_station.elevation,
                wfwx_station_uuid=wfwx_station.wfwx_station_uuid)

            weather_station = WeatherStation(code=wfwx_station.code,
                                             order_of_appearance_in_planning_area_list=station_info[
                                                 'order_of_appearance_in_planning_area_list'],
                                             station_props=station_properties)

            station_info_dict[wfwx_station.code]['station'] = weather_station

            planning_areas_dict[station_info_dict[wfwx_station.code]
                                ['planning_area'].id]['station_objects'].append(weather_station)

    # create PlanningArea objects containing all corresponding WeatherStation objects
    for key, val in planning_areas_dict.items():
        planning_area = PlanningArea(
            id=val['planning_area_record'].id,
            name=val['planning_area_record'].name,
            order_of_appearance_in_list=val['order_of_appearance_in_list'],
            stations=val['station_objects'])
        val['planning_area_object'] = planning_area

    # create FireCentre objects containing all corresponding PlanningArea objects
    for key, val in fire_centres_dict.items():
        planning_area_objects_list = []
        for pa_record in val['planning_area_records']:
            pa_object = planning_areas_dict.get(pa_record.id).get('planning_area_object')
            planning_area_objects_list.append(pa_object)
        fire_centre = FireCentre(
            id=key, name=val['fire_centre_record'].name, planning_areas=planning_area_objects_list)
        fire_centres_list.append(fire_centre)

    return fire_centres_list


def validate_date_range(date_range: Optional[DateRange]) -> DateRange:
    """ Sets the start_date to today if it is None.
    Set the end_date to start_date + 7 days, if it is None."""
    # we don't have a start date, default to now.
    if date_range is None:
        now = app.utils.time.get_pst_now()
        five_days_later = now + timedelta(days=7)
        date_range = DateRange(start_date=date(year=now.year, month=now.month, day=now.day),
                               end_date=date(year=five_days_later.year, month=five_days_later.month, day=five_days_later.day))

    # check if the span exceeds 7, if it does clamp it down to 7 days.
    delta = date_range.end_date - date_range.start_date
    if delta.days > 7:
        date_range.end_date = date_range.start_date + timedelta(days=7)
    return date_range


async def calculate_latest_hfi_results(request: HFIResultRequest):
    "Set up time range and fire centre data for calculating HFI results"

    # pylint: disable=too-many-locals
    logger.info(request)
    # ensure we have valid start and end dates
    valid_date_range = validate_date_range(request.date_range)
    # wf1 talks in terms of timestamps, so we convert the dates to the correct timestamps.
    start_timestamp = int(app.utils.time.get_hour_20_from_date(
        valid_date_range.start_date).timestamp() * 1000)
    end_timestamp = int(app.utils.time.get_hour_20_from_date(valid_date_range.end_date).timestamp() * 1000)

    # pylint: disable=too-many-locals
    async with ClientSession() as session:
        header = await get_auth_header(session)
        # TODO: Enable when fuel type config implemented
        # selected_station_codes = extract_selected_stations(request)

        with get_read_session_scope() as orm_session:
            # Fetching dailies is an expensive operation. When a user is clicking an unclicking stations
            # in the front end, we'd prefer to not change the the call that's going to wfwx so that we can
            # use cached values. So we don't actually filter out the "selected" stations, but rather go
            # get all the stations for this fire centre.
            fire_centre_stations = get_fire_centre_stations(
                orm_session, request.selected_fire_center_id)
            fire_centre_station_code_ids = set()
            area_station_map = {}
            station_fuel_type_map = {}
            for station, fuel_type in fire_centre_stations:
                fire_centre_station_code_ids.add(station.station_code)
                if not station.planning_area_id in area_station_map:
                    area_station_map[station.planning_area_id] = []
                area_station_map[station.planning_area_id].append(station)
                station_fuel_type_map[station.station_code] = fuel_type

        wfwx_stations = await get_wfwx_stations_from_station_codes(
            session, header, list(fire_centre_station_code_ids))

        wfwx_station_ids = [wfwx_station.wfwx_id for wfwx_station in wfwx_stations]
        raw_dailies_generator = await get_raw_dailies_in_range_generator(
            session, header, wfwx_station_ids, start_timestamp, end_timestamp)
        dailies_generator = station_daily_generator(
            raw_dailies_generator, wfwx_stations, station_fuel_type_map)
        dailies = []
        async for station_daily in dailies_generator:
            dailies.append(station_daily)

        prep_delta = valid_date_range.end_date - valid_date_range.start_date
        prep_days = prep_delta.days + 1  # num prep days is inclusive

        results = calculate_hfi_results(request.planning_area_fire_starts,
                                        dailies, prep_days,
                                        request.selected_station_code_ids,
                                        area_station_map,
                                        valid_date_range.start_date)
        return results, valid_date_range


def calculate_hfi_results(planning_area_fire_starts: Mapping[int, FireStartRange],  # pylint: disable=too-many-locals
                          dailies: list,
                          num_prep_days: int,
                          selected_station_codes: List[int],
                          area_station_map: dict,
                          start_date: date) -> List[PlanningAreaResult]:
    """ Computes HFI results based on parameter inputs """
    planning_area_to_dailies: List[PlanningAreaResult] = []

    for area_id in area_station_map.keys():
        stations = area_station_map[area_id]
        area_station_codes = list(map(lambda station: (station.station_code), stations))

        # Filter list of dailies to include only those for the selected stations and area.
        # No need to sort by date, we can't trust that the list doesn't have dates missing - so we
        # have a bit of code that snatches from this list filtering by date.
        area_dailies: List[StationDaily] = list(
            filter(lambda daily, area_station_codes=area_station_codes:
                   (daily.code in area_station_codes and daily.code in selected_station_codes),
                   dailies))

        # Initialize with defaults if empty
        if area_id not in planning_area_fire_starts:
            planning_area_fire_starts[area_id] = [lowest_fire_starts for _ in range(num_prep_days)]
        else:
            # Handle edge case where the provided planning area fire starts doesn't match the number
            # of prep days.
            if len(planning_area_fire_starts[area_id]) < num_prep_days:
                for _ in range(len(planning_area_fire_starts[area_id]), num_prep_days):
                    planning_area_fire_starts[area_id].append(lowest_fire_starts)

        daily_results: List[DailyResult] = []
        all_dailies_valid: bool = True

        for index in range(num_prep_days):
            dailies_date = start_date + timedelta(days=index)
            prep_day_dailies = get_prep_day_dailies(dailies_date, area_dailies)
            daily_fire_starts: FireStartRange = planning_area_fire_starts[area_id][index]
            mean_intensity_group = calculate_mean_intensity(prep_day_dailies)
            prep_level = calculate_prep_level(mean_intensity_group, daily_fire_starts)
            validated_dailies: List[ValidatedStationDaily] = list(
                map(validate_station_daily, prep_day_dailies))
            all_dailies_valid = all(map(lambda validated_daily: (
                validated_daily.valid), validated_dailies))
            daily_result = DailyResult(
                date=dailies_date,
                dailies=validated_dailies,
                fire_starts=daily_fire_starts,
                mean_intensity_group=mean_intensity_group,
                prep_level=prep_level)
            daily_results.append(daily_result)

        highest_daily_intensity_group = calculate_max_intensity_group(
            list(map(lambda daily_result: (daily_result.mean_intensity_group), daily_results)))

        mean_prep_level = calculate_mean_prep_level(
            list(map(lambda daily_result: (daily_result.prep_level), daily_results)),
            num_prep_days)

        planning_area_to_dailies.append(PlanningAreaResult(
            planning_area_id=area_id,
            all_dailies_valid=all_dailies_valid,
            highest_daily_intensity_group=highest_daily_intensity_group,
            mean_prep_level=mean_prep_level,
            daily_results=daily_results))

    return planning_area_to_dailies


def calculate_max_intensity_group(mean_intensity_groups: List[Optional[float]]):
    """ Returns the highest intensity group from a list of values """
    valid_mean_intensity_groups = list(filter(None, mean_intensity_groups))
    return None if len(valid_mean_intensity_groups) == 0 else max(valid_mean_intensity_groups)


def calculate_mean_prep_level(prep_levels: List[Optional[float]], num_prep_days: int):
    """ Returns the mean prep level from a list of values """
    valid_prep_levels = list(filter(None, prep_levels))
    if len(valid_prep_levels) == 0 or len(valid_prep_levels) != num_prep_days:
        return None
    return round(mean(valid_prep_levels))


def calculate_mean_intensity(dailies: List[StationDaily]):
    """ Returns the mean intensity group from a list of values """
    intensity_groups = list(map(lambda daily: (daily.intensity_group), dailies))
    valid_intensity_groups = list(filter(None, intensity_groups))
    if len(valid_intensity_groups) == 0:
        return None
    mean_intensity_group = mean(valid_intensity_groups)
    if round(mean_intensity_group % 1, 1) < 0.8:
        return math.floor(mean_intensity_group)
    return math.ceil(mean_intensity_group)


def calculate_prep_level(mean_intensity_group: Optional[float], fire_starts: FireStartRange):
    """ Returns the prep level based on the MIG and fire starts range """
    if mean_intensity_group is None:
        return None

    rounded_mig = round(mean_intensity_group)
    if rounded_mig == 0:
        return None
    return fire_starts.lookup_table[rounded_mig]


def validate_station_daily(daily: StationDaily):
    """ Returns a validated station daily based on a station daily """
    valids = []
    for attr, value in daily.__dict__.items():
        if attr in required_daily_fields:
            valids.append(value is not None)
    valid = all(valids)
    return ValidatedStationDaily(daily=daily, valid=valid)
