""" Marshals HFI result into structure that jinja can easily
        iterate over for generating the daily PDF sheets
"""
from datetime import datetime
from functools import reduce
from itertools import groupby
import operator
from typing import List, Mapping
from app.schemas.hfi_calc import (DailyPDFData, DailyResult,
                                  HFIResultResponse,
                                  PlanningArea, PlanningAreaResult,
                                  PlanningAreaPDFData,
                                  StationDaily,
                                  StationPDFData, ValidatedStationDaily,
                                  WeatherStation)


def response_2_prep_cycle_jinja_format(result: HFIResultResponse,
                                       planning_area_dict: Mapping[int, PlanningArea],
                                       station_dict: Mapping[int, WeatherStation]):
    """
    Marshals HFI result into structure that jinja can easily
    iterate over for generating the prep cycle PDF sheet
    """
    prep_cycle_pdf_data: List[PlanningAreaPDFData] = []
    for area_result in result.planning_area_hfi_results:

        area_dailies: List[StationDaily] = get_station_dailies(area_result)
        sorted_dates = get_sorted_dates(area_dailies)
        formatted_dates: List[str] = get_formatted_dates(sorted_dates)
        date_range: str = get_date_range_string(sorted_dates)
        station_pdf_data = get_station_pdf_data(area_dailies, station_dict)
        fire_starts_labels = get_fire_start_labels(result, area_result)
        mean_intensity_groups = get_mean_intensity_groups(area_result.daily_results)
        prep_levels = get_prep_levels(area_result.daily_results)

        planning_area_name = planning_area_dict[area_result.planning_area_id].name
        order = planning_area_dict[area_result.planning_area_id].order_of_appearance_in_list
        highest_daily_intensity_group = area_result.highest_daily_intensity_group
        mean_prep_level = area_result.mean_prep_level

        area_pdf_data = PlanningAreaPDFData(planning_area_name=planning_area_name,
                                            order=order,
                                            highest_daily_intensity_group=highest_daily_intensity_group,
                                            mean_prep_level=mean_prep_level,
                                            mean_intensity_groups=mean_intensity_groups,
                                            fire_starts_labels=fire_starts_labels,
                                            prep_levels=prep_levels,
                                            dailies=station_pdf_data)
        prep_cycle_pdf_data.append(area_pdf_data)

    return sorted(prep_cycle_pdf_data, key=operator.attrgetter('order')), formatted_dates, date_range


def get_station_dailies(area_result: PlanningAreaResult):
    """
    Returns the station dailies from the planning area result
    """
    area_validated_dailies: List[ValidatedStationDaily] = reduce(list.__add__, list(
        map(lambda x: x.dailies, area_result.daily_results)))

    # extract just the station daily
    area_dailies: List[StationDaily] = list(map(lambda x: x.daily, area_validated_dailies))
    return area_dailies


def get_sorted_dates(area_dailies: List[StationDaily]) -> List[datetime]:
    """
    Returns the unique dates in sorted order
    """
    unique_dates = list({daily.date for daily in area_dailies})
    return sorted(unique_dates)


def get_formatted_dates(dates: List[datetime]):
    """
    Returns the dates formatted as readable weekday strings
    """
    formatted_dates = []
    for date in dates:
        date_obj = datetime.strptime(str(date), '%Y-%m-%d %H:%M:%S%z')
        formatted_date_string = str(date_obj.strftime("%A %B, %d, %Y"))
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
        return dates[0].date().isoformat()

    return f'{dates[0].date().isoformat()} to {dates[-1].date().isoformat()}'


def get_fire_start_labels(result: HFIResultResponse, area_result: PlanningAreaResult):
    """
    Returns the fire start labels for each planning area on each date
    """
    fire_starts = result.planning_area_fire_starts[area_result.planning_area_id]
    labels = list(map(lambda fs: fs.label, fire_starts))
    return labels


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


def get_station_pdf_data(area_dailies: List[StationDaily],
                         station_dict: Mapping[int, WeatherStation]) -> Mapping[int, List[StationPDFData]]:
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

    data: List[StationPDFData] = []
    for daily in dailies_by_code_and_date:
        station_data = station_dict[daily.code]
        daily_dict = daily.dict()
        daily_dict.update(station_data)
        station_pdf_data = StationPDFData(**daily_dict)
        data.append(station_pdf_data)

    # Sorting dailies into dict keyed by station code
    key = operator.attrgetter('code')
    dailies_by_code = dict((k, list(map(lambda x: x, values)))
                           for k, values in groupby(sorted(data, key=key), key))
    return dailies_by_code


def response_2_daily_jinja_format(result: HFIResultResponse,
                                  planning_area_dict: Mapping[int, PlanningArea],
                                  station_dict: Mapping[int, WeatherStation]):
    """
    Marshals HFI result into structure that jinja can easily
    iterate over for generating the daily PDF sheets
    """
    # pylint: disable=too-many-locals
    # TODO: refactor to simplify

    daily_pdf_data: List[DailyPDFData] = []
    for area_result in result.planning_area_hfi_results:
        fire_starts_range = result.planning_area_fire_starts[area_result.planning_area_id]
        for idx, daily_result in enumerate(area_result.daily_results):
            dailies: List[StationDaily] = list(map(lambda x: x.daily, daily_result.dailies))
            full_dailies: List[StationPDFData] = []
            for daily in dailies:
                station_data = station_dict[daily.code]
                merged = daily.dict()
                merged.update(station_data)
                full_daily = StationPDFData(**merged)
                full_dailies.append(full_daily)
            fire_starts = fire_starts_range[idx]
            planning_area_name = planning_area_dict[area_result.planning_area_id].name
            daily_data = DailyPDFData(planning_area_name=planning_area_name,
                                      highest_daily_intensity_group=area_result.highest_daily_intensity_group,
                                      mean_prep_level=area_result.mean_prep_level,
                                      fire_starts=fire_starts.label,
                                      date=daily_result.date.isoformat(),
                                      dailies=full_dailies)
            daily_pdf_data.append(daily_data)

    key = operator.attrgetter('date')
    daily_pdf_data_by_date = dict((k, list(map(lambda x: x, values)))
                                  for k, values in groupby(sorted(daily_pdf_data, key=key), key))
    return daily_pdf_data_by_date
