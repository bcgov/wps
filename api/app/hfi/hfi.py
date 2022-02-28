""" HFI calculation logic """

from operator import attrgetter
from statistics import mean
from typing import Mapping, Optional, List
from datetime import date, timedelta
from app.schemas.hfi_calc import (DailyResult,
                                  FireStartRange,
                                  PlanningAreaResult,
                                  StationDaily,
                                  ValidatedStationDaily,
                                  required_daily_fields,
                                  lowest_fire_starts)
from app.utils.time import get_hour_20_from_date


def get_prep_day_dailies(dailies_date: date, area_dailies: List[StationDaily]) -> List[StationDaily]:
    """ Return all the dailies (that's noon, or 20 hours UTC) for a given date """
    dailies_date_time = get_hour_20_from_date(dailies_date)
    return list(filter(lambda daily: (daily.date == dailies_date_time), area_dailies))


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
        area_dailies: List[StationDaily] = list(
            filter(lambda daily:
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
            list(map(lambda daily_result: (daily_result.prep_level), daily_results)))

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
    # TODO: establish, if there are any invalid intensity groups, do we return None?
    return None if len(valid_mean_intensity_groups) == 0 else max(valid_mean_intensity_groups)


def calculate_mean_prep_level(prep_levels: List[Optional[float]]):
    """ Returns the mean prep level from a list of values """
    valid_prep_levels = list(filter(None, prep_levels))
    # TODO: establish, if there are any invalid pre levels, do we return None?
    return None if len(valid_prep_levels) == 0 else round(mean(valid_prep_levels))


def calculate_mean_intensity(dailies: List[StationDaily]):
    """ Returns the mean intensity group from a list of values """
    intensity_groups = list(map(lambda daily: (daily.intensity_group), dailies))
    valid_intensity_groups = list(filter(None, intensity_groups))
    return None if len(valid_intensity_groups) == 0 else round(mean(valid_intensity_groups), 1)


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
