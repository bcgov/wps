"""Generate a daily PDF"""
from datetime import date
from typing import List, Mapping
import pdfkit
from jinja2 import Environment, FunctionLoader
from app.schemas.hfi_calc import FireCentre, HFIResultResponse, PDFFileDetails, PlanningArea, WeatherStation
from app.hfi.daily_template import str_daily_template, CSS_PATH
from app.hfi.pdf_data_formatter import response_2_daily_jinja_format

# Loads template as string from a function
# See: https://jinja.palletsprojects.com/en/3.0.x/api/?highlight=functionloader#jinja2.FunctionLoader
jinja_env = Environment(loader=FunctionLoader(str_daily_template), autoescape=True)


def generate_daily_pdf(
    result: HFIResultResponse,
    fire_centres: List[FireCentre],
    username: str
) -> PDFFileDetails:
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

    rendered_output: str = ''

    template = jinja_env.get_template('daily_template')
    daily_pdf_data_by_date = response_2_daily_jinja_format(
        result,
        planning_area_dict,
        station_dict)
    rendered_output += template.render(
        daily_pdf_data_by_date=daily_pdf_data_by_date,
        fire_centre_name=fire_centre_name)

    options = {
        'page-size': 'Tabloid'
    }

    pdf_bytes: bytes = pdfkit.from_string(input=rendered_output, options=options, css=CSS_PATH)
    filename = get_filename(fire_centre_name, date.today(), username)

    return PDFFileDetails(pdf=pdf_bytes, filename=filename)


def get_filename(firecentre_name: str, date_generated: date, idir: str) -> str:
    return firecentre_name.replace(" ", "").upper() + \
        "_HFICALCULATOR_" + \
        date_generated.isoformat() + \
        "_" + \
        idir.upper() + \
        ".pdf"
