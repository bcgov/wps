""" HFI calculation logic """

from itertools import groupby
from operator import attrgetter
from statistics import mean
from typing import Mapping, Optional, List
from app.schemas.hfi_calc import (DailyResult,
                                  FireCentre,
                                  FireStartRange,
                                  PlanningAreaResult,
                                  StationDaily,
                                  ValidatedStationDaily,
                                  required_daily_fields,
                                  lowest_fire_starts)


def calculate_hfi_results(fire_centre: Optional[FireCentre],  # pylint: disable=too-many-locals
                          planning_area_fire_starts: Mapping[str, FireStartRange],
                          dailies: List[StationDaily],
                          num_prep_days: int,
                          selected_station_codes: List[int]):
    """ Computes HFI results based on parameter inputs """
    planning_area_to_dailies: Mapping[str, PlanningAreaResult] = {}
    if fire_centre is None:
        return planning_area_to_dailies

    for area in fire_centre.planning_areas:
        area_station_codes = map(lambda station: (station.code), area.stations)

        # Marshall dailies in chronological order,
        # that are part of the planning area and are selected
        area_dailies: List[StationDaily] = sorted(
            list(filter(lambda daily, area_station_codes=area_station_codes:
                        (daily.code in area_station_codes and daily.code in selected_station_codes),
                        dailies)),
            key=attrgetter('date'))

        # Group dailies into lists by date
        area_dailies_by_date = [list(g) for _, g in groupby(area_dailies, lambda area_daily: area_daily.date)]

        # Take only the number of days requested for
        prep_week_dailies = area_dailies_by_date[:num_prep_days]

        # Initialize with defaults if empty
        if area.name not in planning_area_fire_starts:
            planning_area_fire_starts[area.name] = [lowest_fire_starts for _ in range(num_prep_days)]

        daily_results: List[DailyResult] = []
        all_dailies_valid: bool = True
        for index, prep_day_dailies in enumerate(prep_week_dailies):
            daily_fire_starts: FireStartRange = planning_area_fire_starts[area.name][index]
            mean_intensity_group = calculate_mean_intensity(prep_day_dailies)
            prep_level = calculate_prep_level(mean_intensity_group, daily_fire_starts)
            validated_dailies: List[ValidatedStationDaily] = list(
                map(validate_station_daily, prep_day_dailies))
            all_dailies_valid = all(map(lambda validated_daily: (validated_daily.valid), validated_dailies))
            daily_result: DailyResult = DailyResult(
                dateISO=prep_day_dailies[0].date.isoformat(),
                dailies=validated_dailies,
                fire_starts=daily_fire_starts,
                mean_intensity_group=mean_intensity_group,
                prep_level=prep_level)
            daily_results.append(daily_result)

        highest_daily_intensity_group = calculate_max_intensity_group(
            list(map(lambda daily_result: (daily_result.mean_intensity_group), daily_results)))

        mean_prep_level = calculate_mean_prep_level(
            list(map(lambda daily_result: (daily_result.prep_level), daily_results)))

        planning_area_to_dailies[area.name] = PlanningAreaResult(
            all_dailies_valid=all_dailies_valid,
            highest_daily_intensity_group=highest_daily_intensity_group,
            mean_prep_level=mean_prep_level,
            daily_results=daily_results)

    return planning_area_to_dailies


def calculate_max_intensity_group(mean_intensity_groups: List[Optional[float]]):
    """ Returns the highest intensity group from a list of values """
    valid_mean_intensity_groups = list(filter(None, mean_intensity_groups))
    return None if len(valid_mean_intensity_groups) == 0 else max(mean_intensity_groups)


def calculate_mean_prep_level(prep_levels: List[Optional[float]]):
    """ Returns the mean prep level from a list of values """
    valid_prep_levels = list(filter(None, prep_levels))
    return None if len(valid_prep_levels) == 0 else mean(valid_prep_levels)


def calculate_mean_intensity(dailies: List[StationDaily]):
    """ Returns the mean intensity group from a list of values """
    intensity_groups = list(map(lambda daily: (daily.intensity_group), dailies))
    valid_intensity_groups = list(filter(None, intensity_groups))
    return None if len(valid_intensity_groups) == 0 else \
        round((10 * sum(valid_intensity_groups) / len(valid_intensity_groups))) / 10


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
