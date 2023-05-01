""" HFI calculation logic """
import math
import logging
from typing import Optional, List, Dict, Tuple
from datetime import date, datetime, timedelta, timezone
from statistics import mean
from aiohttp.client import ClientSession
from sqlalchemy.orm import Session
import app
from app.db.database import get_read_session_scope
from app.db.models.hfi_calc import FuelType as FuelTypeModel
from app.fire_behaviour.cffdrs import CFFDRSException
from app.fire_behaviour.prediction import (
    FireBehaviourPredictionInputError, calculate_fire_behaviour_prediction, FireBehaviourPrediction)
from app.schemas.hfi_calc import (DailyResult, DateRange,
                                  FireStartRange, HFIResultRequest,
                                  PlanningAreaResult,
                                  StationDaily, StationInfo,
                                  ValidatedStationDaily,
                                  required_daily_fields)
from app.schemas.hfi_calc import (WeatherStationProperties,
                                  FuelType as FuelTypeSchema, FireCentre, PlanningArea, WeatherStation)
from app.fire_behaviour.fuel_types import FUEL_TYPE_DEFAULTS, FuelTypeEnum
from app.utils.time import get_hour_20_from_date, get_pst_now
from app.wildfire_one.schema_parsers import WFWXWeatherStation
from app.wildfire_one.wfwx_api import (get_auth_header, get_stations_by_codes,
                                       get_wfwx_stations_from_station_codes,
                                       get_raw_dailies_in_range_generator)
from app.db.crud.hfi_calc import (get_fire_weather_stations,
                                  get_fire_centre_fire_start_ranges,
                                  get_fire_start_lookup,
                                  get_fuel_types)

logger = logging.getLogger(__name__)


def generate_station_daily(raw_daily: dict,
                           station: WFWXWeatherStation,
                           fuel_type: FuelTypeModel) -> StationDaily:
    """ Transform from the raw daily json object returned by wf1, to our daily object.
    """
    pc = fuel_type.percentage_conifer
    pdf = fuel_type.percentage_dead_fir
    # we use the fuel type lookup to get default values.
    cbh = FUEL_TYPE_DEFAULTS[fuel_type.fuel_type_code]["CBH"]
    cfl = FUEL_TYPE_DEFAULTS[fuel_type.fuel_type_code]["CFL"]
    isi = raw_daily.get('initialSpreadIndex', None)
    bui = raw_daily.get('buildUpIndex', None)
    ffmc = raw_daily.get('fineFuelMoistureCode', None)
    cc = raw_daily.get('grasslandCuring', None)
    wind_speed = raw_daily.get('windSpeed', None)

    try:
        fire_behaviour_prediction = calculate_fire_behaviour_prediction(
            latitude=station.lat,
            longitude=station.long,
            elevation=station.elevation,
            fuel_type=FuelTypeEnum[fuel_type.fuel_type_code],
            bui=bui,
            ffmc=ffmc,
            wind_speed=wind_speed,
            cc=cc,
            pc=pc,
            isi=isi,
            pdf=pdf,
            cbh=cbh,
            cfl=cfl)
    except (FireBehaviourPredictionInputError, CFFDRSException) as error:
        logger.info("Error calculating fire behaviour prediction for station %s : %s", station.code, error)
        fire_behaviour_prediction = FireBehaviourPrediction(None, None, None, None, None)

    return StationDaily(
        code=station.code,
        date=datetime.fromtimestamp(raw_daily['weatherTimestamp'] / 1000, tz=timezone.utc),
        status=raw_daily.get('recordType', {}).get('id', None),
        temperature=raw_daily.get('temperature', None),
        relative_humidity=raw_daily.get('relativeHumidity', None),
        wind_speed=raw_daily.get('windSpeed', None),
        wind_direction=raw_daily.get('windDirection', None),
        precipitation=raw_daily.get('precipitation', None),
        grass_cure_percentage=raw_daily.get('grasslandCuring', None),
        ffmc=ffmc,
        dmc=raw_daily.get('duffMoistureCode', None),
        dc=raw_daily.get('droughtCode', None),
        fwi=raw_daily.get('fireWeatherIndex', None),
        # Danger class possible values: 1, 2, 3, 4, and 5. Where 1 is the lowest, and 5 is the highest
        # This is the same for the dangerGrassland and dangerScrub,
        # but those values aren’t really used anywhere,
        # just calculated and stored along with the forest danger rating
        # You can see current stations/rating on this page here:
        # https://wfapps.nrs.gov.bc.ca/pub/wfwx-danger-summary-war/dangerSummary
        danger_class=raw_daily.get('dangerForest', None),
        isi=isi,
        bui=bui,
        rate_of_spread=fire_behaviour_prediction.ros,
        hfi=fire_behaviour_prediction.hfi,
        observation_valid=raw_daily.get('observationValidInd', None),
        observation_valid_comment=raw_daily.get('observationValidComment', None),
        intensity_group=fire_behaviour_prediction.intensity_group,
        sixty_minute_fire_size=fire_behaviour_prediction.sixty_minute_fire_size,
        fire_type=fire_behaviour_prediction.fire_type,
        error=raw_daily.get('observationValidInd', None),
        error_message=raw_daily.get('observationValidComment', None),
        last_updated=datetime.fromtimestamp(raw_daily['lastEntityUpdateTimestamp'] / 1000, tz=timezone.utc)
    )


def get_prep_day_dailies(dailies_date: date, area_dailies: List[StationDaily]) -> List[StationDaily]:
    """ Return all the dailies (that's noon, or 20 hours UTC) for a given date """
    dailies_date_time = get_hour_20_from_date(dailies_date)
    return list(filter(lambda daily: (daily.date == dailies_date_time), area_dailies))


async def hydrate_fire_centres():
    """Get detailed fire_centres from db and WFWX"""

    with get_read_session_scope() as session:
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
            station_info = {
                'fuel_type': FuelTypeSchema(
                    id=fuel_type_record.id,
                    abbrev=fuel_type_record.abbrev,
                    fuel_type_code=fuel_type_record.fuel_type_code,
                    description=fuel_type_record.description,
                    percentage_conifer=fuel_type_record.percentage_conifer,
                    percentage_dead_fir=fuel_type_record.percentage_dead_fir),
                'order_of_appearance_in_planning_area_list': station_record.order_of_appearance_in_planning_area_list,
                'planning_area': planning_area_record,
                'fire_centre': fire_centre_record
            }
            if station_info_dict.get(station_record.station_code) is None:
                station_info_dict[station_record.station_code] = [station_info]
            else:
                station_info_dict[station_record.station_code].append(station_info)

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
            # Combine everything.
            station_properties = WeatherStationProperties(
                name=wfwx_station.name,
                elevation=wfwx_station.elevation,
                wfwx_station_uuid=wfwx_station.wfwx_station_uuid)

            for station_info in station_info_dict[wfwx_station.code]:
                weather_station = WeatherStation(code=wfwx_station.code,
                                                 order_of_appearance_in_planning_area_list=station_info[
                                                     'order_of_appearance_in_planning_area_list'],
                                                 station_props=station_properties)
                station_info['station'] = weather_station
                for planning_station in station_info_dict[wfwx_station.code]:
                    existing_station_codes = [
                        s.code for s in planning_areas_dict[planning_station['planning_area'].id]['station_objects']]

                    if weather_station.code not in existing_station_codes:
                        planning_areas_dict[planning_station['planning_area'].id]['station_objects'].append(
                            weather_station)

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


async def calculate_latest_hfi_results(
        orm_session: Session,
        request: HFIResultRequest,
        fire_centre_fire_start_ranges: List[FireStartRange]) -> Tuple[List[PlanningAreaResult], DateRange]:
    """Set up time range and fire centre data for calculating HFI results"""
    # ensure we have valid start and end dates
    valid_date_range = validate_date_range(request.date_range)
    # wf1 talks in terms of timestamps, so we convert the dates to the correct timestamps.
    start_timestamp = int(app.utils.time.get_hour_20_from_date(
        valid_date_range.start_date).timestamp() * 1000)
    end_timestamp = int(app.utils.time.get_hour_20_from_date(valid_date_range.end_date).timestamp() * 1000)

    async with ClientSession() as session:
        header = await get_auth_header(session)
        # Fetching dailies is an expensive operation. When a user is clicking and unclicking stations
        # in the front end, we'd prefer to not change the call that's going to wfwx so that we can
        # use cached values. So we don't actually filter out the "selected" stations, but rather go
        # get all the stations for this fire centre.

        fire_centre_stations = [
            station for area_stations in request.planning_area_station_info.values() for station in area_stations]
        fire_centre_station_code_ids = set()
        for station in fire_centre_stations:
            fire_centre_station_code_ids.add(station.station_code)

        fire_start_lookup = build_fire_start_prep_level_lookup(orm_session)

        wfwx_stations: List[WFWXWeatherStation] = await get_wfwx_stations_from_station_codes(
            session, header, list(fire_centre_station_code_ids))

        wfwx_station_ids = [wfwx_station.wfwx_id for wfwx_station in wfwx_stations]
        raw_dailies_generator = await get_raw_dailies_in_range_generator(
            session, header, wfwx_station_ids, start_timestamp, end_timestamp)
        raw_dailies: List[dict] = [raw_daily async for raw_daily in raw_dailies_generator]
        fuel_type_lookup: Dict[int, FuelTypeModel] = generate_fuel_type_lookup(orm_session)

        results = calculate_hfi_results(fuel_type_lookup,
                                        fire_centre_fire_start_ranges,
                                        request.planning_area_fire_starts,
                                        fire_start_lookup,
                                        wfwx_stations,
                                        raw_dailies,
                                        valid_date_range.days_in_range(),
                                        request.planning_area_station_info,
                                        valid_date_range.start_date)
        return results, valid_date_range


def build_fire_start_prep_level_lookup(orm_session) -> Dict[int, Dict[int, int]]:
    """ Build a mapping from fire start range id to mean intensity group to prep level """
    fire_start_lookup_records = get_fire_start_lookup(orm_session)
    fire_start_lookup = {}
    for lookup in fire_start_lookup_records:
        if lookup.fire_start_range_id not in fire_start_lookup:
            fire_start_lookup[lookup.fire_start_range_id] = {}
        fire_start_lookup[lookup.fire_start_range_id][lookup.mean_intensity_group] = lookup.prep_level
    return fire_start_lookup


def load_fire_start_ranges(orm_session, fire_centre_id: int) -> List[FireStartRange]:
    """ Fetch the fire start ranges for a fire centre from the database, and return them as a list of
    schema objects.
    """
    return [FireStartRange(
        label=fire_start_range.label,
        id=fire_start_range.id)
        for fire_start_range in get_fire_centre_fire_start_ranges(orm_session, fire_centre_id)]


def initialize_planning_area_fire_starts(
        planning_area_fire_starts: Dict[int, FireStartRange],
        planning_area_id: int,
        num_prep_days: int,
        lowest_fire_starts: FireStartRange):
    """ Load up the planning area fire start ranges with default values.
    """
    if planning_area_id not in planning_area_fire_starts:
        planning_area_fire_starts[planning_area_id] = [lowest_fire_starts for _ in range(num_prep_days)]
    else:
        # Handle edge case where the provided planning area fire starts doesn't match the number
        # of prep days.
        if len(planning_area_fire_starts[planning_area_id]) < num_prep_days:
            for _ in range(len(planning_area_fire_starts[planning_area_id]), num_prep_days):
                planning_area_fire_starts[planning_area_id].append(lowest_fire_starts)


def calculate_daily_results(num_prep_days: int,
                            start_date: date,
                            area_dailies: List[StationDaily],
                            planning_area_fire_starts: Dict[int, FireStartRange],
                            area_id: int,
                            fire_start_lookup: Dict[int, Dict[int, int]],
                            num_unique_station_codes: int) -> Tuple[List[DailyResult], bool]:
    """ Calculate the daily results for a planning area."""
    daily_results: List[DailyResult] = []
    for index in range(num_prep_days):
        dailies_date = start_date + timedelta(days=index)
        prep_day_dailies = get_prep_day_dailies(dailies_date, area_dailies)
        daily_fire_starts: FireStartRange = planning_area_fire_starts[area_id][index]
        mean_intensity_group = calculate_mean_intensity(prep_day_dailies, num_unique_station_codes)
        prep_level = calculate_prep_level(mean_intensity_group, daily_fire_starts, fire_start_lookup)
        validated_dailies: List[ValidatedStationDaily] = list(map(validate_station_daily, prep_day_dailies))
        # check if all validated_dailies are valid.
        valids = [v.valid for v in validated_dailies]
        all_dailies_valid = all(valids)
        daily_result = DailyResult(
            date=dailies_date,
            dailies=validated_dailies,
            fire_starts=daily_fire_starts,
            mean_intensity_group=mean_intensity_group,
            prep_level=prep_level)
        daily_results.append(daily_result)
    return daily_results, all_dailies_valid


def generate_fuel_type_lookup(orm_session: Session) -> Dict[int, FuelTypeModel]:
    """ Generate a lookup table for fuel types. """
    fuel_types = get_fuel_types(orm_session)
    return {fuel_type.id: fuel_type for fuel_type in fuel_types}


def calculate_station_dailies(
        raw_dailies: List[dict],
        station_info_list: List[StationInfo],
        station_lookup: Dict[str, WFWXWeatherStation],
        fuel_type_lookup: Dict[int, FuelTypeModel]) -> List[StationDaily]:
    """ Build a list of dailies with results from the fire behaviour calculations. """
    area_dailies: List[StationDaily] = []

    selected_station_codes = [
        station.station_code for station in filter(
            lambda station: (station.selected), station_info_list)]
    station_info_lookup = {station.station_code: station for station in station_info_list}

    for raw_daily in raw_dailies:
        wfwx_station_id = raw_daily['stationId']
        wfwx_station = station_lookup[wfwx_station_id]
        # Filter list of dailies to include only those for the selected stations and area.
        # No need to sort by date, we can't trust that the list doesn't have dates missing - so we
        # have a bit of code that snatches from this list filtering by date.
        if wfwx_station.code in selected_station_codes:
            station_info: StationInfo = station_info_lookup[wfwx_station.code]
            fuel_type = fuel_type_lookup[station_info.fuel_type_id]
            area_dailies.append(generate_station_daily(raw_daily, wfwx_station, fuel_type))
    return area_dailies


def calculate_hfi_results(fuel_type_lookup: Dict[int, FuelTypeModel],
                          fire_start_ranges: List[FireStartRange],
                          planning_area_fire_starts: Dict[int, FireStartRange],
                          fire_start_lookup: Dict[int, Dict[int, int]],
                          wfwx_stations: List[WFWXWeatherStation],
                          raw_dailies: List[dict],
                          num_prep_days: int,
                          planning_area_station_info: Dict[int, List[StationInfo]],
                          start_date: date) -> List[PlanningAreaResult]:
    """ Computes HFI results based on parameter inputs """
    planning_area_to_dailies: List[PlanningAreaResult] = []

    station_lookup: Dict[str, WFWXWeatherStation] = {station.wfwx_id: station for station in wfwx_stations}

    for area_id in planning_area_station_info.keys():

        area_dailies = calculate_station_dailies(raw_dailies,
                                                 planning_area_station_info[area_id],
                                                 station_lookup,
                                                 fuel_type_lookup)

        # Initialize with defaults if empty/wrong length
        # TODO: Sometimes initialize_planning_area_fire_starts is called twice. Look into this once
        # endpoint re-factor is complete.
        lowest_fire_starts = fire_start_ranges[0]
        initialize_planning_area_fire_starts(
            planning_area_fire_starts,
            area_id,
            num_prep_days,
            lowest_fire_starts)

        all_dailies_valid: bool = True
        num_unique_station_codes = len([
            station.station_code for station in filter(
                lambda station: (station.selected), planning_area_station_info[area_id])])

        (daily_results,
         all_dailies_valid) = calculate_daily_results(num_prep_days,
                                                      start_date,
                                                      area_dailies,
                                                      planning_area_fire_starts,
                                                      area_id,
                                                      fire_start_lookup,
                                                      num_unique_station_codes)

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


def calculate_mean_intensity(dailies: List[StationDaily], num_of_station_codes: int):
    """ Returns the mean intensity group from a list of values """
    # If there are less dailies than there are unique station codes in the planning area,
    # it means that some stations are entirely missing data for the day, so MIG can't
    # be calculated.
    if len(dailies) != num_of_station_codes:
        return None
    intensity_groups = list(map(lambda daily: (daily.intensity_group), dailies))
    valid_intensity_groups = list(filter(None, intensity_groups))
    # If some intensity groups are invalid, can't calculate mean intensity group. Should display error
    if len(valid_intensity_groups) != len(dailies) or len(valid_intensity_groups) == 0:
        return None
    mean_intensity_group = mean(valid_intensity_groups)
    if round(mean_intensity_group % 1, 1) < 0.8:
        return math.floor(mean_intensity_group)
    return math.ceil(mean_intensity_group)


def calculate_prep_level(
        mean_intensity_group: Optional[float],
        fire_starts: FireStartRange,
        fire_start_lookup: Dict[int, Dict[int, int]]) -> Optional[int]:
    """ Returns the prep level based on the MIG and fire starts range. """
    if mean_intensity_group is None:
        return None

    rounded_mig = round(mean_intensity_group)
    if rounded_mig == 0:
        return None
    return fire_start_lookup[fire_starts.id][rounded_mig]


def validate_station_daily(daily: StationDaily):
    """ Returns a validated station daily based on a station daily """
    valids = []
    for attr, value in daily.__dict__.items():
        if attr in required_daily_fields:
            valids.append(value is not None)
    valid = all(valids)
    return ValidatedStationDaily(daily=daily, valid=valid)


def validate_date_range(date_range: Optional[DateRange]) -> DateRange:
    """
    Date ranges are inclusive: [start, end]
    No range or start_date sets range to 5 days
    Clamps range to 7 days if over 7 days
    Clamps range to 1 day if under 1 day
    """
    # we don't have a start date, default to now.
    start_date = date_range.start_date if date_range is not None else None
    end_date = date_range.end_date if date_range is not None else None
    if start_date is None:
        now = get_pst_now()
        start_date = date(year=now.year, month=now.month, day=now.day)
    # don't have an end date, default to start date + 4 days.
    if end_date is None:
        end_date = start_date + timedelta(days=4)
    # check if the span exceeds 6, if it does clamp it down to 6 days.
    delta = end_date - start_date
    if delta.days > 6:
        end_date = start_date + timedelta(days=6)
    # guarantee at least one day is selected.
    if delta.days < 1:
        end_date = start_date
    return DateRange(start_date=start_date, end_date=end_date)
