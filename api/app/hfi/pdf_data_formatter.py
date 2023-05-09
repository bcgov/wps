""" Marshals HFI result into structure that jinja can easily
        iterate over for generating the daily PDF sheets
"""
from datetime import date, datetime, timedelta
from functools import reduce
from itertools import groupby
import copy
import operator
from typing import List, Dict

from app.schemas.hfi_calc import (DailyTablePlanningAreaPDFData, DailyResult, DateRange,
                                  HFIResultResponse,
                                  PlanningArea, PlanningAreaResult,
                                  PrepTablePlanningAreaPDFData,
                                  StationDaily, StationInfo,
                                  StationPDFData, ValidatedStationDaily,
                                  WeatherStation)
from app.schemas.shared import FuelType


def response_2_prep_cycle_jinja_format(result: HFIResultResponse,
                                       planning_area_dict: Dict[int, PlanningArea],
                                       station_dict: Dict[int, WeatherStation],
                                       fuel_types: Dict[int, FuelType]):
    """
    Marshals HFI result into structure that jinja can easily
    iterate over for generating the prep cycle PDF sheet
    """
    sorted_dates = get_sorted_dates(result.date_range)
    formatted_dates: List[str] = get_formatted_dates(sorted_dates)
    date_range: str = get_date_range_string(sorted_dates)
    prep_cycle_pdf_data: List[PrepTablePlanningAreaPDFData] = []
    for area_result in result.planning_area_hfi_results:
        area_dailies: List[StationDaily] = get_station_dailies(area_result)
        planning_area_station_info = result.planning_area_station_info[area_result.planning_area_id]
        station_pdf_data = get_station_pdf_data(
            area_dailies, station_dict, fuel_types, planning_area_station_info)
        fire_starts_labels = get_fire_start_labels(area_result.daily_results)
        mean_intensity_groups = get_mean_intensity_groups(area_result.daily_results)
        prep_levels = get_prep_levels(area_result.daily_results)

        planning_area_name = planning_area_dict[area_result.planning_area_id].name
        order = planning_area_dict[area_result.planning_area_id].order_of_appearance_in_list
        highest_intensity_group = area_result.highest_daily_intensity_group
        mean_prep_level = area_result.mean_prep_level

        area_pdf_data = PrepTablePlanningAreaPDFData(planning_area_name=planning_area_name,
                                                     order=order,
                                                     highest_daily_intensity_group=highest_intensity_group,
                                                     mean_prep_level=mean_prep_level,
                                                     mean_intensity_groups=mean_intensity_groups,
                                                     fire_starts_labels=fire_starts_labels,
                                                     prep_levels=prep_levels,
                                                     dailies=station_pdf_data)
        prep_cycle_pdf_data.append(area_pdf_data)

    return sorted(prep_cycle_pdf_data, key=operator.attrgetter('order')), formatted_dates, date_range


def get_station_dailies(area_result: PlanningAreaResult):
    """
    Flatten the lists of dailies from area daily results then return them all
    """
    area_validated_dailies: List[ValidatedStationDaily] = reduce(list.__add__, list(
        map(lambda x: x.dailies, area_result.daily_results)))

    # extract just the station daily
    area_dailies: List[StationDaily] = list(map(lambda x: x.daily, area_validated_dailies))
    return area_dailies


def get_sorted_dates(date_range: DateRange) -> List[date]:
    """
    Returns the unique dates in sorted order
    """
    dates = []
    current_date = date_range.start_date
    while current_date != date_range.end_date:
        dates.append(copy.deepcopy(current_date))
        current_date = current_date + timedelta(days=1)

    # last date
    dates.append(copy.deepcopy(current_date))
    return dates


def get_formatted_dates(dates: List[date]) -> List[str]:
    """
    Returns the dates formatted as readable weekday strings
    """
    formatted_dates = []
    for raw_date in dates:
        formatted_date_string = raw_date.strftime("%A %B %d, %Y")
        formatted_dates.append(formatted_date_string)

    return formatted_dates


def get_date_range_string(dates: List[datetime]):
    """
    Returns a formatted date range string of form "<start iso> to <end iso>
    Assumes input is sorted in desired order
    """
    if len(dates) == 0:
        return ''

    if len(dates) == 1:
        return dates[0].isoformat()

    return f'{dates[0].isoformat()} to {dates[-1].isoformat()}'


def get_fire_start_labels(daily_results: List[DailyResult]):
    """
    Returns the fire start labels for each planning area on each date
    """
    return list(map(lambda daily_result: daily_result.fire_starts.label, daily_results))


def get_prep_levels(daily_results: List[DailyResult]):
    """
    Returns the prep levels from the daily results
    """
    return list(map(lambda daily_result: daily_result.prep_level, daily_results))


def get_mean_intensity_groups(daily_results: List[DailyResult]):
    """
    Returns the mean intensity groups from the daily results
    """
    return list(map(lambda daily_result: daily_result.mean_intensity_group, daily_results))


def get_merged_station_data(
        station_dict: Dict[int, WeatherStation],
        dailies: List[StationDaily],
        fuel_types: Dict[int, FuelType],
        planning_area_station_info: List[StationInfo]):
    """
    Returns all the weather station and daily data we have for a station
    """
    all_station_pdf_data: List[StationPDFData] = []
    # We do a bunch of null checks here because station_dict is built from
    # stations we retrieve from WF1, while the dailies come from the HFI request
    # which can have an different set of stations
    for daily in dailies:
        station_data = station_dict.get(daily.code, None)
        daily_dict = daily.dict()
        if station_data is not None:
            daily_dict.update(station_data)
        station_info: StationInfo = next(
            station_info for
            station_info in planning_area_station_info if station_info.station_code == daily.code)
        daily_dict['fuel_type'] = fuel_types[station_info.fuel_type_id]
        if station_data is not None:
            station_pdf_data = StationPDFData(**daily_dict)
            all_station_pdf_data.append(station_pdf_data)
    return all_station_pdf_data


def get_station_pdf_data(area_dailies: List[StationDaily],
                         station_dict: Dict[int, WeatherStation],
                         fuel_types: Dict[int, FuelType],
                         planning_area_station_info: List[StationInfo]) -> Dict[int, List[StationPDFData]]:
    """
    Merges and sorts station dailies and weather station properties
    expected in prep cycle PDF template order
    """

    # group dailies by station code
    get_attr = operator.attrgetter('code')
    area_dailies_by_code = [list(g) for _, g in groupby(sorted(area_dailies, key=get_attr), get_attr)]

    # for each group, in place sort by date
    for daily_list in area_dailies_by_code:
        daily_list.sort(key=lambda x: x.date)

    # Flat list of station daily grouped by code and ordered by date
    # e.g. [{code: 1, date: 1, code: 1, date: 2, ..., code: 2, date: 1, code: 2, date: 2, ...}]
    dailies_by_code_and_date: List[StationDaily] = reduce(list.__add__, area_dailies_by_code, [])

    station_daily_pdf_data = get_merged_station_data(
        station_dict, dailies_by_code_and_date, fuel_types, planning_area_station_info)

    # Sorting dailies into dict keyed by station code
    key = operator.attrgetter('code')
    dailies_by_code = dict((k, list(map(lambda x: x, values)))
                           for k, values in groupby(sorted(station_daily_pdf_data, key=key), key))
    return dailies_by_code


def response_2_daily_jinja_format(result: HFIResultResponse,
                                  planning_area_dict: Dict[int, PlanningArea],
                                  station_dict: Dict[int, WeatherStation],
                                  fuel_types: Dict[int, FuelType]):
    """
    Marshals HFI result into structure that jinja can easily
    iterate over for generating the daily PDF sheets
    """
    daily_pdf_data: List[DailyTablePlanningAreaPDFData] = []
    for area_result in result.planning_area_hfi_results:
        for daily_result in area_result.daily_results:
            dailies: List[StationDaily] = list(map(lambda x: x.daily, daily_result.dailies))
            station_daily_pdf_data: List[StationPDFData] = get_merged_station_data(
                station_dict, dailies, fuel_types,
                result.planning_area_station_info[area_result.planning_area_id])
            planning_area_name = planning_area_dict[area_result.planning_area_id].name
            order = planning_area_dict[area_result.planning_area_id].order_of_appearance_in_list
            daily_data = DailyTablePlanningAreaPDFData(planning_area_name=planning_area_name,
                                                       order=order,
                                                       mean_intensity_group=daily_result.mean_intensity_group,
                                                       prep_level=daily_result.prep_level,
                                                       fire_starts=daily_result.fire_starts.label,
                                                       date=daily_result.date.isoformat(),
                                                       dailies=station_daily_pdf_data)
            daily_pdf_data.append(daily_data)

    daily_pdf_data.sort(key=lambda k: (k.date, k.order))
    daily_pdf_data_by_date = dict((k, list(map(lambda x: x, values)))
                                  for k, values in groupby(
                                      daily_pdf_data,
                                      operator.attrgetter('date')))
    return daily_pdf_data_by_date
