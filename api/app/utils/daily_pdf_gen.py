"""Generate a daily PDF"""
import os
from typing import List, Mapping
import pdfkit
from jinja2 import Environment, FunctionLoader
from app.schemas.hfi_calc import FireCentre, HFIResultResponse, PlanningArea, WeatherStation
from app.utils.daily_template import str_daily_template
from app.utils.pdf_data_formatter import response_2_daily_jinja_format

daily_rendered_path = os.path.join(os.path.dirname(__file__), 'daily_rendered.html')
output_file_path = os.path.join(os.path.dirname(__file__), "out.pdf")

jinja_env = Environment(loader=FunctionLoader(str_daily_template), autoescape=True)


def generate_daily_pdf(result: HFIResultResponse, fire_centres: List[FireCentre]) -> bool:
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

    with open(daily_rendered_path, 'w', encoding='UTF-8') as new_page:
        template = jinja_env.get_template('daily_template')
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
