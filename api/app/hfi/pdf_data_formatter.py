""" Marshals HFI result into structure that jinja can easily
        iterate over for generating the daily PDF sheets
"""
import datetime
from functools import reduce
from itertools import groupby
import operator
from typing import List, Mapping
from app.hfi.hfi_calc import validate_station_daily
from app.schemas.hfi_calc import (DailyPDFData,
                                  HFIResultResponse,
                                  PlanningArea, PrepCyclePDFData,
                                  StationDaily,
                                  StationPDFData,
                                  WeatherStation)


def response_2_prep_cycle_jinja_format(result: HFIResultResponse):
    """ Marshals HFI result into structure that jinja can easily
        iterate over for generating the prep cycle PDF sheet
     """
    prep_cycle_pdf_data: List[PrepCyclePDFData] = []
    for area_result in result.planning_area_hfi_results:
        # all validated dailies from planning area result
        area_validated_dailies: List[validate_station_daily] = reduce(list.__add__, list(
            map(lambda x: x.dailies, area_result.daily_results)))

        # extract just the station daily
        area_dailies: List[StationDaily] = list(map(lambda x: x.daily, area_validated_dailies))

        # group dailies by station code
        get_attr = operator.attrgetter('code')
        area_dailies_by_code = [list(g) for _, g in groupby(sorted(area_dailies, key=get_attr), get_attr)]

        # for each group, in place sort by date
        for daily_list in area_dailies_by_code:
            daily_list.sort(key=lambda x: x.date)

        # Flat list of station daily grouped by code and ordered by date
        # e.g. [{code: 1, date: 1, code: 1, date: 2, ..., code: 2, date: 1, code: 2, date: 2, ...}]
        areas_by_code_and_date = reduce(list.__add__, area_dailies_by_code)

        # Sorting dailies into dict keyed by station code
        key = operator.attrgetter('code')
        dailies_by_code = dict((k, list(map(lambda x: x, values)))
                               for k, values in groupby(sorted(areas_by_code_and_date, key=key), key))

        # TODO: Get planning area name, not just id
        area_pdf_data = PrepCyclePDFData(planningAreaName=area_result.planning_area_id,
                                         dailies=dailies_by_code)
        prep_cycle_pdf_data.append(area_pdf_data)

        # List of dates for prep period
        dates = []
        for area in prep_cycle_pdf_data:
            for dailies in area.dailies.values():
                for daily in dailies:
                    date_obj = datetime.datetime.strptime(str(daily.date), '%Y-%m-%d %H:%M:%S%z')
                    formatted_date_string = str(date_obj.strftime("%A %B, %d, %Y"))
                    dates.append(formatted_date_string)
                break
            break

    return prep_cycle_pdf_data, dates


def response_2_daily_jinja_format(result: HFIResultResponse,
                                  planning_area_dict: Mapping[int, PlanningArea],
                                  station_dict: Mapping[int, WeatherStation]):  # pylint: disable=line-too-long
    """ Marshals HFI result into structure that jinja can easily
        iterate over for generating the daily PDF sheets
     """

    daily_pdf_data: List[DailyPDFData] = []
    for area_result in result.planning_area_hfi_results:
        fire_starts_range = result.planning_area_fire_starts[area_result.planning_area_id]
        days_total = len(area_result.daily_results)
        for j, daily_result in enumerate(area_result.daily_results):
            dailies: List[StationDaily] = list(map(lambda x: x.daily, daily_result.dailies))
            full_dailies: List[StationPDFData] = []
            for daily in dailies:
                station_data = station_dict[daily.code]
                merged = daily.dict()
                merged.update(station_data)
                full_daily = StationPDFData(**merged)
                full_dailies.append(full_daily)
            fire_starts = fire_starts_range[j]
            planning_area_name = planning_area_dict[area_result.planning_area_id].name
            daily_data = DailyPDFData(planning_area_name=planning_area_name,
                                      highest_daily_intensity_group=area_result.highest_daily_intensity_group,
                                      mean_prep_level=area_result.mean_prep_level,
                                      fire_starts=fire_starts.label,
                                      days_total=days_total,
                                      day=j,
                                      date=daily_result.date.isoformat(),
                                      dailies=full_dailies)
            daily_pdf_data.append(daily_data)

    key = operator.attrgetter('date')
    daily_pdf_data_by_date = dict((k, list(map(lambda x: x, values)))
                                  for k, values in groupby(sorted(daily_pdf_data, key=key), key))
    return daily_pdf_data_by_date
