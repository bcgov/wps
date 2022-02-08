""" HFI calculation logic """

from itertools import groupby
from operator import attrgetter
from statistics import mean
from typing import Mapping, Optional, List
from app.schemas.hfi_calc import DailyResult, FireCentre, FireStartRange, PlanningAreaResult, ValidatedStationDaily, lowest_fire_starts
from app.schemas.hfi_calc import FireStartRange, StationDaily


def calculate_hfi_results(fire_centre: Optional[FireCentre],
                          planning_area_fire_starts: Mapping[str, FireStartRange],
                          dailies: List[StationDaily],
                          num_prep_days: int,
                          selected_station_codes: List[int]):
    """ Computes HFI results based on parameter inputs """
    planning_area_to_dailies: Mapping[str, PlanningAreaResult] = dict()
    if fire_centre is None:
        return planning_area_to_dailies

    for area in fire_centre.planning_areas:
        area_station_codes = map(lambda station: (station.code), area.stations)
        area_dailies: List[StationDaily] = sorted(
            list(filter(lambda daily: (daily.code in area_station_codes and daily.code in selected_station_codes),
                        dailies)),
            key=attrgetter('date'))

        area_dailies_by_date = [list(g) for _, g in groupby(area_dailies, lambda area_daily: area_daily.date)]
        # Initialize with defaults if empty
        if area.name not in planning_area_fire_starts:
            planning_area_fire_starts[area.name] = [lowest_fire_starts for _ in range(num_prep_days)]

        dailies_in_prep = area_dailies_by_date[:num_prep_days]

        daily_results: List[DailyResult] = []
        all_dailies_valid: bool = True
        for index, prep_day_dailies in enumerate(dailies_in_prep):
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
    return None if len(mean_intensity_groups) == 0 else max(mean_intensity_groups)


def calculate_mean_prep_level(prep_levels: List[Optional[float]]):
    valid_prep_levels = list(filter(None, prep_levels))
    num_prep_levels = len(valid_prep_levels)
    if num_prep_levels == 0:
        return None
    return mean(valid_prep_levels)


def calculate_mean_intensity(dailies: List[StationDaily]):
    return 0


def calculate_prep_level(mean_intensity_group: Optional[float], fire_starts: FireStartRange):
    if mean_intensity_group is None:
        return None

    rounded_mig = round(mean_intensity_group)
    if rounded_mig == 0:
        return None
    return fire_starts.lookup_table[rounded_mig]


def validate_station_daily(daily: StationDaily):
    return ValidatedStationDaily(
        code=daily.code,
        status=daily.status,
        temperature=daily.temperature,
        relative_humidity=daily.relative_humidity,
        wind_speed=daily.wind_speed,
        wind_direction=daily.wind_direction,
        grass_cure_percentage=daily.grass_cure_percentage,
        precipitation=daily.precipitation,
        ffmc=daily.ffmc,
        dmc=daily.dmc,
        dc=daily.dc,
        isi=daily.isi,
        bui=daily.bui,
        fwi=daily.fwi,
        danger_class=daily.danger_class,
        observation_valid=daily.observation_valid,
        observation_valid_comment=daily.observation_valid_comment,
        rate_of_spread=daily.rate_of_spread,
        hfi=daily.hfi,
        intensity_group=daily.intensity_group,
        sixty_minute_fire_size=daily.sixty_minute_fire_size,
        fire_type=daily.fire_type,
        error=daily.error,
        error_message=daily.error_message,
        date=daily.date,
        valid=True)
