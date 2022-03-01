from itertools import groupby
import pdfkit
import json
from jinja2 import Template

from app.schemas.hfi_calc import HFIResultResponse

daily_template_path = "api/app/utils/daily_template.html"
daily_rendered_path = "api/app/utils/daily_rendered.html"

output_file_path = "api/app/utils/out.pdf"


def generate_daily_pdf(result: HFIResultResponse):
    with open(daily_template_path, 'r') as daily_template:
        template = Template(daily_template.read())
        with open(daily_rendered_path, 'w') as new_page:
            for index, area_result in enumerate(result.planning_area_hfi_results):
                new_page.write(template.render(
                    areaResult=area_result.dict(),
                    fire_centre_id=result.selected_fire_center_id))

    options = {
        'page-size': 'Tabloid'
    }

    return pdfkit.from_file(daily_rendered_path,
                            output_file_path, options)


class JinjaAreaResult:
    def __init__(self, date, planning_area_id, dailies, fire_starts, prep_level, mean_intensity_group):
        self.date = date
        self.planning_area_id = planning_area_id
        self.dailies = dailies
        self.fire_starts = fire_starts
        self.prep_level = prep_level
        self.mean_intensity_group = mean_intensity_group


class JinjaAreaResult:
    def __init__(self, date, planning_area_id, dailies, fire_starts, prep_level, mean_intensity_group):
        self.date = date
        self.planning_area_id = planning_area_id
        self.dailies = dailies
        self.fire_starts = fire_starts
        self.prep_level = prep_level
        self.mean_intensity_group = mean_intensity_group


def get_jinja_area_data(result: HFIResultResponse):
    jinja_dailies = []
    for area_result in result.planning_area_hfi_results:
        # Group daily results into lists by date
        daily_result_by_date = [list(g) for _, g in groupby(
            area_result.daily_results, lambda daily_result: daily_result.dateISO)]

        jinja_results = list(map(lambda daily_result: (JinjaAreaResult(date=daily_result.dateISO,
                                                       planning_area_id=area_result.planning_area_id,
                                                       dailies=daily_result.dailies,
                                                       prep_level=area_result.mean_prep_level,
                                                       mean_intensity_group=area_result.highest_daily_intensity_group
                                                                       )), area_result.daily_results))
