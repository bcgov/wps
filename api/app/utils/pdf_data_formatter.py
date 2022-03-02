from functools import reduce
from itertools import groupby
import operator
from typing import List
from app.schemas.hfi_calc import (DailyPDFData,
                                  HFIResultResponse,
                                  PrepCyclePDFData,
                                  StationDaily,
                                  ValidatedStationDaily)


def response_2_prep_cycle_jinja_format(result: HFIResultResponse):
    """ Marshals HFI result into structure that jinja can easily
        iterate over for generating the prep cycle PDF sheet
     """
    prep_cycle_pdf_data: List[PrepCyclePDFData] = []
    for area_result in result.planning_area_hfi_results:
        # all validated dailies from planning area result
        area_validated_dailies: List[ValidatedStationDaily] = reduce(list.__add__, list(
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

        # TODO: Get planning area name, not just id
        area_pdf_data = PrepCyclePDFData(planningAreaName=area_result.planning_area_id,
                                         dailies=areas_by_code_and_date)
        prep_cycle_pdf_data.append(area_pdf_data)

    return prep_cycle_pdf_data


def response_2_daily_jinja_format(result: HFIResultResponse):
    """ Marshals HFI result into structure that jinja can easily
        iterate over for generating the daily PDF sheets
     """

    daily_pdf_data: List[DailyPDFData] = []
    for area_result in result.planning_area_hfi_results:
        days_total = len(area_result.daily_results)
        for index, daily_result in enumerate(area_result.daily_results):
            dailies: List[StationDaily] = list(map(lambda x: x.daily, daily_result.dailies))

            # TODO: Get planning area name, not just id
            daily_data = DailyPDFData(planning_area_name=area_result.planning_area_id,
                                      days_total=days_total,
                                      day=index,
                                      date=daily_result.dateISO,
                                      dailies=dailies)
            daily_pdf_data.append(daily_data)

    key = operator.attrgetter('date')
    daily_pdf_data_by_date = dict((k, list(map(lambda x: x, values)))
                                  for k, values in groupby(sorted(daily_pdf_data, key=key), key))
    return daily_pdf_data_by_date
