"""Generate a daily PDF"""
from typing import List, Mapping
import pdfkit
from jinja2 import Environment, FunctionLoader
from app.schemas.hfi_calc import FireCentre, HFIResultResponse, PlanningArea, WeatherStation
from app.hfi.pdf_template import PDFTemplateName, get_template, CSS_PATH
from app.hfi.pdf_data_formatter import response_2_daily_jinja_format, response_2_prep_cycle_jinja_format

# Loads template as string from a function
# See: https://jinja.palletsprojects.com/en/3.0.x/api/?highlight=functionloader#jinja2.FunctionLoader
jinja_env = Environment(loader=FunctionLoader(get_template), autoescape=True)


def generate_pdf(result: HFIResultResponse, fire_centres: List[FireCentre]) -> bytes:
    """Generates the full PDF based on the HFIResultResponse"""

    rendered_output: str = ''
    rendered_output += generate_prep(result)
    rendered_output += generate_daily(result, fire_centres)

    options = {
        'page-size': 'Tabloid'
    }

    pdf_bytes: bytes = pdfkit.from_string(input=rendered_output, options=options, css=CSS_PATH)

    return pdf_bytes


def generate_prep(result: HFIResultResponse):
    """Generates the prep cycle portion of the PDF"""
    prep_pdf_data, dates = response_2_prep_cycle_jinja_format(result)
    template = jinja_env.get_template(PDFTemplateName.PREP.value)

    return template.render(
        planningAreas=prep_pdf_data,
        prepDays=dates)


def generate_daily(result: HFIResultResponse, fire_centres: List[FireCentre]) -> str:
    """Generates the daily portion of the PDF"""
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

    template = jinja_env.get_template(PDFTemplateName.DAILY.value)
    daily_pdf_data_by_date = response_2_daily_jinja_format(
        result,
        planning_area_dict,
        station_dict)
    return template.render(
        daily_pdf_data_by_date=daily_pdf_data_by_date,
        fire_centre_name=fire_centre_name)
