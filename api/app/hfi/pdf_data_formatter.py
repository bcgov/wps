""" Marshals HFI result into structure that jinja can easily
        iterate over for generating the daily PDF sheets
"""
from itertools import groupby
import operator
from typing import List, Mapping
from app.schemas.hfi_calc import (DailyPDFData,
                                  HFIResultResponse,
                                  PlanningArea,
                                  StationDaily,
                                  StationPDFData,
                                  WeatherStation)


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
