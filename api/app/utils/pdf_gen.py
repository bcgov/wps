from functools import reduce
from itertools import groupby
from typing import List
import pdfkit
from jinja2 import Template
import json

from app.schemas.hfi_calc import (HFIResultResponse,
                                  PrepCyclePDFData,
                                  StationDaily,
                                  ValidatedStationDaily)

json_file = open('/Users/jforeman/Workspace/wps/api/app/utils/test_json.json')
html = open('/Users/jforeman/Workspace/wps/api/app/templates/template1.html').read()

data = json.load(json_file)
template = Template(html)


def response_2_prep_cycle_jinja_format(result: HFIResultResponse):
    prep_cycle_pdf_data: List[PrepCyclePDFData] = []
    for area_result in result.planning_area_hfi_results:
        # all validated dailies from planning area result
        area_validated_dailies: List[ValidatedStationDaily] = reduce(list.__add__, list(
            map(lambda x: x.dailies, area_result.daily_results)))

        # extract just the station daily
        area_dailies: List[StationDaily] = list(map(lambda x: x.daily, area_validated_dailies))

        # Group dailies by station code
        area_dailies_by_code: List[List[StationDaily]] = [list(g) for _, g in groupby(
            area_dailies, lambda area_daily: area_daily.code)]

        # For each group, in place sort by date
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


with open('/Users/jforeman/Workspace/wps/api/app/utils/rendered_template.html', 'w') as new_page:
    new_page.write(template.render(planningAreas=data['planning_area_hfi_results']))


options = {
    'page-size': 'Tabloid'
}

pdfkit.from_file('/Users/jforeman/Workspace/wps/api/app/utils/rendered_template.html',
                 '/Users/jforeman/Workspace/wps/api/app/utils/out.pdf', options)
