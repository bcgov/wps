"""Generate a daily PDF"""
from typing import List, Mapping
import pdfkit
from jinja2 import Template

from app.schemas.hfi_calc import FireCentre, HFIResultResponse, PlanningArea, WeatherStation
from app.utils.pdf_data_formatter import response_2_daily_jinja_format

daily_template_path = "api/app/utils/daily_template.html"
daily_rendered_path = "api/app/utils/daily_rendered.html"

output_file_path = "api/app/utils/out.pdf"


def generate_daily_pdf(result: HFIResultResponse, fire_centres: List[FireCentre]):
    """Generate a daily PDF"""
    # Shift hydrated fire centres into dicts keyed by ids
    fire_centre_dict: Mapping[int, FireCentre] = {}
    planning_area_dict: Mapping[int, PlanningArea] = {}
    station_dict: Mapping[int, WeatherStation] = {}
    for fire_centre in fire_centres:
        fire_centre_dict[fire_centre.id] = fire_centre
        for planning_area in fire_centre.planning_areas:
            planning_area_dict[planning_area.id] = planning_area
            for station in planning_area.stations:
                station_dict[station.code] = station

    fire_centre_name = fire_centre_dict[result.selected_fire_center_id].name
    with open(daily_template_path, 'r') as daily_template, open(daily_rendered_path, 'w') as new_page:
        template = Template(daily_template.read())
        daily_pdf_data_by_date = response_2_daily_jinja_format(
            result,
            planning_area_dict,
            station_dict)
        new_page.write(template.render(
            daily_pdf_data_by_date=daily_pdf_data_by_date,
            fire_centre_name=fire_centre_name))

    options = {
        'page-size': 'Tabloid'
    }

    return pdfkit.from_file(daily_rendered_path,
                            output_file_path, options)
