"""HFI calculation logic"""

import logging
import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from itertools import groupby
from statistics import mean
from typing import Dict, List, Optional, Set, Tuple

import wps_shared.utils.time
from aiohttp.client import ClientSession
from sqlalchemy.orm import Session
from wps_shared.db.crud.hfi_calc import (
    get_fire_centre_fire_start_ranges,
    get_fire_centre_station_codes,
    get_fire_start_lookup,
    get_fire_weather_stations,
    get_fuel_types,
)
from wps_shared.db.database import get_read_session_scope
from wps_shared.db.models.hfi_calc import FuelType as FuelTypeModel
from wps_shared.db.models.hfi_calc import PlanningWeatherStation
from wps_shared.fuel_types import FUEL_TYPE_DEFAULTS, FuelTypeEnum
from wps_shared.schemas.hfi_calc import (
    DailyResult,
    DateRange,
    FireCentre,
    FireStartRange,
    HFIResultRequest,
    PlanningArea,
    PlanningAreaResult,
    StationDaily,
    StationInfo,
    ValidatedStationDaily,
    WeatherStation,
    WeatherStationProperties,
    required_daily_fields,
)
from wps_shared.utils.time import get_hour_20_from_date, get_pst_now
from wps_shared.wildfire_one.wfwx_api import create_wfwx_api
from wps_wf1.models import WFWXWeatherStation, WeatherStation as WFWXWeatherStationDetails

from app.fire_behaviour.cffdrs import CFFDRSException
from app.fire_behaviour.prediction import (
    FireBehaviourPrediction,
    FireBehaviourPredictionInputError,
    calculate_fire_behaviour_prediction,
)

logger = logging.getLogger(__name__)


def generate_station_daily(
    raw_daily: dict, station: WFWXWeatherStation, fuel_type: FuelTypeModel
) -> StationDaily:
    """Transform from the raw daily json object returned by wf1, to our daily object."""
    pc = fuel_type.percentage_conifer
    pdf = fuel_type.percentage_dead_fir
    # we use the fuel type lookup to get default values.
    cbh = FUEL_TYPE_DEFAULTS[fuel_type.fuel_type_code]["CBH"]
    cfl = FUEL_TYPE_DEFAULTS[fuel_type.fuel_type_code]["CFL"]
    isi = raw_daily.get("initialSpreadIndex", None)
    bui = raw_daily.get("buildUpIndex", None)
    ffmc = raw_daily.get("fineFuelMoistureCode", None)
    cc = raw_daily.get("grasslandCuring", None)
    wind_speed = raw_daily.get("windSpeed", None)

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
            cfl=cfl,
        )
    except (FireBehaviourPredictionInputError, CFFDRSException) as error:
        logger.info(
            "Error calculating fire behaviour prediction for station %s : %s", station.code, error
        )
        fire_behaviour_prediction = FireBehaviourPrediction(None, None, None, None, None)

    return StationDaily(
        code=station.code,
        date=datetime.fromtimestamp(raw_daily["weatherTimestamp"] / 1000, tz=timezone.utc),
        status=raw_daily.get("recordType", {}).get("id", None),
        temperature=raw_daily.get("temperature", None),
        relative_humidity=raw_daily.get("relativeHumidity", None),
        wind_speed=raw_daily.get("windSpeed", None),
        wind_direction=raw_daily.get("windDirection", None),
        precipitation=raw_daily.get("precipitation", None),
        grass_cure_percentage=raw_daily.get("grasslandCuring", None),
        ffmc=ffmc,
        dmc=raw_daily.get("duffMoistureCode", None),
        dc=raw_daily.get("droughtCode", None),
        fwi=raw_daily.get("fireWeatherIndex", None),
        # Danger class possible values: 1, 2, 3, 4, and 5. Where 1 is the lowest, and 5 is the highest
        # This is the same for the dangerGrassland and dangerScrub,
        # but those values aren’t really used anywhere,
        # just calculated and stored along with the forest danger rating
        # You can see current stations/rating on this page here:
        # https://wfapps.nrs.gov.bc.ca/pub/wfwx-danger-summary-war/dangerSummary
        danger_class=raw_daily.get("dangerForest", None),
        isi=isi,
        bui=bui,
        rate_of_spread=fire_behaviour_prediction.ros,
        hfi=fire_behaviour_prediction.hfi,
        observation_valid=raw_daily.get("observationValidInd", None),
        observation_valid_comment=raw_daily.get("observationValidComment", None),
        intensity_group=fire_behaviour_prediction.intensity_group,
        sixty_minute_fire_size=fire_behaviour_prediction.sixty_minute_fire_size,
        fire_type=fire_behaviour_prediction.fire_type,
        error=raw_daily.get("observationValidInd", None),
        error_message=raw_daily.get("observationValidComment", None),
        last_updated=datetime.fromtimestamp(
            raw_daily["lastEntityUpdateTimestamp"] / 1000, tz=timezone.utc
        ),
    )


def get_prep_day_dailies(
    dailies_date: date, area_dailies: List[StationDaily]
) -> List[StationDaily]:
    """Return all the dailies (that's noon, or 20 hours UTC) for a given date"""
    dailies_date_time = get_hour_20_from_date(dailies_date)
    return list(filter(lambda daily: (daily.date == dailies_date_time), area_dailies))


def get_hydrated_stations(
    stations: List[PlanningWeatherStation], stations_by_code: Dict[int, WFWXWeatherStationDetails]
):
    """
    Merges all details of stations from our database and the WFWX API together.

    :param stations: the database representation of weather stations
    :param stations_by_code: WFWX representation of weather stations keyed by station code
    :return: a list of all the hydrated stations
    """
    hydrated_stations = []
    for station in stations:
        wfwx_station = stations_by_code.get(station.station_code, None)
        if wfwx_station is not None:
            hydrated_stations.append(
                WeatherStation(
                    code=wfwx_station.code,
                    order_of_appearance_in_planning_area_list=station.order_of_appearance_in_planning_area_list,
                    station_props=WeatherStationProperties(
                        name=wfwx_station.name,
                        elevation=wfwx_station.elevation,
                        wfwx_station_uuid=wfwx_station.wfwx_station_uuid,
                    ),
                )
            )
    return hydrated_stations


async def hydrate_fire_centres():
    """
    Merges all details of fire centres, including their planning areas and
    weather stations together from both the database and the WFWX API.

    :return: a list of all the hydrated fire centres
    """
    with get_read_session_scope() as session:
        # Fetch all fire weather stations from the database.
        rows = get_fire_weather_stations(session)

        # Sort by the attribute 'planning_area_id' of the first element of the tuple
        sorted_rows = sorted(rows, key=lambda row: row[0].planning_area_id)
        # Now group by the same attribute after sorting
        stations_by_area = groupby(sorted_rows, key=lambda row: row[0].planning_area_id)

        station_codes = [station.station_code for (station, _, __, ___) in rows]
        # TODO: Could this use wps_shared.stations.get_stations_by_codes
        async with ClientSession() as session:
            wfwx_api = create_wfwx_api(session)
            wfwx_stations_data = await wfwx_api.get_stations_by_codes(list(set(station_codes)))
        stations_by_code: Dict[int, WFWXWeatherStationDetails] = {
            station.code: station for station in wfwx_stations_data
        }

        planning_areas_by_fire_centre_id = defaultdict(list)
        fire_centres_by_id = {fire_centre.id: fire_centre for (_, __, ___, fire_centre) in rows}

        for _, records in stations_by_area:
            stations_with_planning_areas = [
                (station, planning_area) for (station, _, planning_area, ___) in list(records)
            ]
            stations, planning_areas = zip(*stations_with_planning_areas)
            planning_area = planning_areas[0]
            hydrated_stations = get_hydrated_stations(stations, stations_by_code)
            fire_centre_id = planning_area.fire_centre_id
            planning_areas_by_fire_centre_id[fire_centre_id].append(
                PlanningArea(
                    id=planning_area.id,
                    fire_centre_id=planning_area.fire_centre_id,
                    name=planning_area.name,
                    order_of_appearance_in_list=planning_area.order_of_appearance_in_list,
                    stations=hydrated_stations,
                )
            )

        hydrated_fire_centres = []

        for fire_centre_id, fire_centre in fire_centres_by_id.items():
            planning_areas = planning_areas_by_fire_centre_id.get(fire_centre_id, [])
            hydrated_fire_centres.append(
                FireCentre(id=fire_centre.id, name=fire_centre.name, planning_areas=planning_areas)
            )

        return hydrated_fire_centres


async def calculate_latest_hfi_results(
    orm_session: Session,
    request: HFIResultRequest,
    fire_centre_fire_start_ranges: List[FireStartRange],
) -> Tuple[List[PlanningAreaResult], DateRange]:
    """Set up time range and fire centre data for calculating HFI results"""
    # ensure we have valid start and end dates
    valid_date_range = validate_date_range(request.date_range)
    # wf1 talks in terms of timestamps, so we convert the dates to the correct timestamps.
    start_timestamp = int(
        wps_shared.utils.time.get_hour_20_from_date(valid_date_range.start_date).timestamp() * 1000
    )
    end_timestamp = int(
        wps_shared.utils.time.get_hour_20_from_date(valid_date_range.end_date).timestamp() * 1000
    )

    async with ClientSession() as session:
        # Fetching dailies is an expensive operation. When a user is clicking and unclicking stations
        # in the front end, we'd prefer to not change the call that's going to wfwx so that we can
        # use cached values. So we don't actually filter out the "selected" stations, but rather go
        # get all the stations for this fire centre.

        fire_centre_stations = [
            station
            for area_stations in request.planning_area_station_info.values()
            for station in area_stations
        ]
        fire_centre_station_code_ids = set()
        for station in fire_centre_stations:
            fire_centre_station_code_ids.add(station.station_code)

        fire_start_lookup = build_fire_start_prep_level_lookup(orm_session)

        fire_centre_station_codes = get_fire_centre_station_codes()
        wfwx_api = create_wfwx_api(session)
        wfwx_stations = await wfwx_api.get_wfwx_stations_from_station_codes(
            list(fire_centre_station_code_ids), fire_centre_station_codes
        )

        wfwx_station_ids = [wfwx_station.wfwx_id for wfwx_station in wfwx_stations]
        raw_dailies_generator = await wfwx_api.get_raw_dailies_in_range_generator(
            wfwx_station_ids, start_timestamp, end_timestamp
        )
        raw_dailies: List[dict] = [raw_daily async for raw_daily in raw_dailies_generator]
        fuel_type_lookup: Dict[int, FuelTypeModel] = generate_fuel_type_lookup(orm_session)

        results = calculate_hfi_results(
            fuel_type_lookup,
            fire_centre_fire_start_ranges,
            request.planning_area_fire_starts,
            fire_start_lookup,
            wfwx_stations,
            raw_dailies,
            valid_date_range.days_in_range(),
            request.planning_area_station_info,
            valid_date_range.start_date,
        )
        return results, valid_date_range


def build_fire_start_prep_level_lookup(orm_session) -> Dict[int, Dict[int, int]]:
    """Build a mapping from fire start range id to mean intensity group to prep level"""
    fire_start_lookup_records = get_fire_start_lookup(orm_session)
    fire_start_lookup = {}
    for lookup in fire_start_lookup_records:
        if lookup.fire_start_range_id not in fire_start_lookup:
            fire_start_lookup[lookup.fire_start_range_id] = {}
        fire_start_lookup[lookup.fire_start_range_id][lookup.mean_intensity_group] = (
            lookup.prep_level
        )
    return fire_start_lookup


def load_fire_start_ranges(orm_session, fire_centre_id: int) -> List[FireStartRange]:
    """Fetch the fire start ranges for a fire centre from the database, and return them as a list of
    schema objects.
    """
    return [
        FireStartRange(label=fire_start_range.label, id=fire_start_range.id)
        for fire_start_range in get_fire_centre_fire_start_ranges(orm_session, fire_centre_id)
    ]


def initialize_planning_area_fire_starts(
    planning_area_fire_starts: Dict[int, FireStartRange],
    planning_area_id: int,
    num_prep_days: int,
    lowest_fire_starts: FireStartRange,
):
    """Load up the planning area fire start ranges with default values."""
    if planning_area_id not in planning_area_fire_starts:
        planning_area_fire_starts[planning_area_id] = [
            lowest_fire_starts for _ in range(num_prep_days)
        ]
    else:
        # Handle edge case where the provided planning area fire starts doesn't match the number
        # of prep days.
        if len(planning_area_fire_starts[planning_area_id]) < num_prep_days:
            for _ in range(len(planning_area_fire_starts[planning_area_id]), num_prep_days):
                planning_area_fire_starts[planning_area_id].append(lowest_fire_starts)


def calculate_daily_results(
    num_prep_days: int,
    start_date: date,
    area_dailies: List[StationDaily],
    planning_area_fire_starts: Dict[int, FireStartRange],
    area_id: int,
    fire_start_lookup: Dict[int, Dict[int, int]],
    num_unique_station_codes: int,
) -> Tuple[List[DailyResult], bool]:
    """Calculate the daily results for a planning area."""
    daily_results: List[DailyResult] = []
    for index in range(num_prep_days):
        dailies_date = start_date + timedelta(days=index)
        prep_day_dailies = get_prep_day_dailies(dailies_date, area_dailies)
        daily_fire_starts: FireStartRange = planning_area_fire_starts[area_id][index]
        mean_intensity_group = calculate_mean_intensity(prep_day_dailies, num_unique_station_codes)
        prep_level = calculate_prep_level(
            mean_intensity_group, daily_fire_starts, fire_start_lookup
        )
        validated_dailies: List[ValidatedStationDaily] = list(
            map(validate_station_daily, prep_day_dailies)
        )
        # check if all validated_dailies are valid.
        valids = [v.valid for v in validated_dailies]
        all_dailies_valid = all(valids)
        daily_result = DailyResult(
            date=dailies_date,
            dailies=validated_dailies,
            fire_starts=daily_fire_starts,
            mean_intensity_group=mean_intensity_group,
            prep_level=prep_level,
        )
        daily_results.append(daily_result)
    return daily_results, all_dailies_valid


def generate_fuel_type_lookup(orm_session: Session) -> Dict[int, FuelTypeModel]:
    """Generate a lookup table for fuel types."""
    fuel_types = get_fuel_types(orm_session)
    return {fuel_type.id: fuel_type for fuel_type in fuel_types}


def calculate_station_dailies(
    raw_dailies: List[dict],
    station_info_list: List[StationInfo],
    station_lookup: Dict[str, WFWXWeatherStation],
    fuel_type_lookup: Dict[int, FuelTypeModel],
) -> List[StationDaily]:
    """Build a list of dailies with results from the fire behaviour calculations."""
    area_dailies: List[StationDaily] = []

    selected_station_codes = [
        station.station_code
        for station in filter(lambda station: (station.selected), station_info_list)
    ]
    station_info_lookup = {station.station_code: station for station in station_info_list}

    for raw_daily in raw_dailies:
        wfwx_station_id = raw_daily["stationId"]
        wfwx_station = station_lookup[wfwx_station_id]
        # Filter list of dailies to include only those for the selected stations and area.
        # No need to sort by date, we can't trust that the list doesn't have dates missing - so we
        # have a bit of code that snatches from this list filtering by date.
        if wfwx_station.code in selected_station_codes:
            station_info: StationInfo = station_info_lookup[wfwx_station.code]
            fuel_type = fuel_type_lookup[station_info.fuel_type_id]
            area_dailies.append(generate_station_daily(raw_daily, wfwx_station, fuel_type))
    return area_dailies


def calculate_hfi_results(
    fuel_type_lookup: Dict[int, FuelTypeModel],
    fire_start_ranges: List[FireStartRange],
    planning_area_fire_starts: Dict[int, FireStartRange],
    fire_start_lookup: Dict[int, Dict[int, int]],
    wfwx_stations: List[WFWXWeatherStation],
    raw_dailies: List[dict],
    num_prep_days: int,
    planning_area_station_info: Dict[int, List[StationInfo]],
    start_date: date,
) -> List[PlanningAreaResult]:
    """Computes HFI results based on parameter inputs"""
    planning_area_to_dailies: List[PlanningAreaResult] = []

    station_lookup: Dict[str, WFWXWeatherStation] = {
        station.wfwx_id: station for station in wfwx_stations
    }
    wfwx_station_codes: Set[int] = set([station.code for station in wfwx_stations])

    for area_id in planning_area_station_info.keys():
        area_dailies = calculate_station_dailies(
            raw_dailies, planning_area_station_info[area_id], station_lookup, fuel_type_lookup
        )

        # Initialize with defaults if empty/wrong length
        # TODO: Sometimes initialize_planning_area_fire_starts is called twice. Look into this once
        # endpoint re-factor is complete.
        lowest_fire_starts = fire_start_ranges[0]
        initialize_planning_area_fire_starts(
            planning_area_fire_starts, area_id, num_prep_days, lowest_fire_starts
        )

        selected_stations = [
            station.station_code
            for station in planning_area_station_info[area_id]
            if station.selected is True and station.station_code in wfwx_station_codes
        ]
        all_dailies_valid: bool = True
        num_unique_station_codes = len(set(selected_stations))

        (daily_results, all_dailies_valid) = calculate_daily_results(
            num_prep_days,
            start_date,
            area_dailies,
            planning_area_fire_starts,
            area_id,
            fire_start_lookup,
            num_unique_station_codes,
        )

        highest_daily_intensity_group = calculate_max_intensity_group(
            list(map(lambda daily_result: (daily_result.mean_intensity_group), daily_results))
        )

        mean_prep_level = calculate_mean_prep_level(
            list(map(lambda daily_result: (daily_result.prep_level), daily_results)), num_prep_days
        )

        planning_area_to_dailies.append(
            PlanningAreaResult(
                planning_area_id=area_id,
                all_dailies_valid=all_dailies_valid,
                highest_daily_intensity_group=highest_daily_intensity_group,
                mean_prep_level=mean_prep_level,
                daily_results=daily_results,
            )
        )

    return planning_area_to_dailies


def calculate_max_intensity_group(mean_intensity_groups: List[Optional[float]]):
    """Returns the highest intensity group from a list of values"""
    valid_mean_intensity_groups = list(filter(None, mean_intensity_groups))
    return None if len(valid_mean_intensity_groups) == 0 else max(valid_mean_intensity_groups)


def calculate_mean_prep_level(prep_levels: List[Optional[float]], num_prep_days: int):
    """Returns the mean prep level from a list of values"""
    valid_prep_levels = list(filter(None, prep_levels))
    if len(valid_prep_levels) == 0 or len(valid_prep_levels) != num_prep_days:
        return None
    return round(mean(valid_prep_levels))


def calculate_mean_intensity(dailies: List[StationDaily], num_of_station_codes: int):
    """Returns the mean intensity group from a list of values"""
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
    fire_start_lookup: Dict[int, Dict[int, int]],
) -> Optional[int]:
    """Returns the prep level based on the MIG and fire starts range."""
    if mean_intensity_group is None:
        return None

    rounded_mig = round(mean_intensity_group)
    if rounded_mig == 0:
        return None
    return fire_start_lookup[fire_starts.id][rounded_mig]


def validate_station_daily(daily: StationDaily):
    """Returns a validated station daily based on a station daily"""
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
