"""Generate a daily PDF"""
import logging
from datetime import date, datetime
from typing import List, Dict, Tuple
import pdfkit
from jinja2 import Environment
from app.db.models.hfi_calc import FuelType
from app.schemas.hfi_calc import FireCentre, HFIResultResponse, PlanningArea, WeatherStation
from app.hfi.pdf_template import PDFTemplateName, CSS_PATH
from app.hfi.pdf_data_formatter import response_2_daily_jinja_format, response_2_prep_cycle_jinja_format


logger = logging.getLogger(__name__)


def generate_html(result: HFIResultResponse,
                  fire_centres: List[FireCentre],
                  idir: str,
                  datetime_generated: datetime,
                  jinja_env: Environment,
                  fuel_types: Dict[int, FuelType]) -> Tuple[str, str]:
    """Generates the full HTML based on the HFIResultResponse"""
    fire_centre_dict, planning_area_dict, station_dict = build_mappings(fire_centres)
    fire_centre_name = fire_centre_dict[result.selected_fire_center_id].name

    rendered_output = generate_prep(result,
                                    idir,
                                    datetime_generated,
                                    planning_area_dict,
                                    station_dict,
                                    fire_centre_name,
                                    jinja_env,
                                    fuel_types)
    rendered_output += generate_daily(result,
                                      idir,
                                      datetime_generated,
                                      planning_area_dict,
                                      station_dict,
                                      fire_centre_name,
                                      jinja_env,
                                      fuel_types)

    return rendered_output, fire_centre_name


def generate_pdf(result: HFIResultResponse,
                 fire_centres: List[FireCentre],
                 idir: str,
                 datetime_generated: datetime,
                 jinja_env: Environment,
                 fuel_types: Dict[int, FuelType]) -> Tuple[bytes, str]:
    """Generates the full PDF based on the HFIResultResponse"""
    rendered_output, fire_centre_name = generate_html(result,
                                                      fire_centres,
                                                      idir,
                                                      datetime_generated,
                                                      jinja_env,
                                                      fuel_types)

    left_footer = f'Exported on {datetime_generated.isoformat()} by {idir} | https://psu.nrs.gov.bc.ca/hfi-calculator'
    options = {
        'page-size': 'Letter',
        'orientation': 'Landscape',
        'margin-left': '7mm',
        'margin-right': '7mm',
        'footer-left': left_footer,
        'footer-right': '[page] of [topage]',
        'footer-font-name': 'BCSans',
        'footer-font-size': '6'
    }

    pdf_bytes: bytes = pdfkit.from_string(input=rendered_output, options=options, css=CSS_PATH)
    pdf_filename = get_pdf_filename(fire_centre_name, datetime_generated.date(), idir)

    return pdf_bytes, pdf_filename


def generate_prep(result: HFIResultResponse,
                  idir: str,
                  datetime_generated: datetime,
                  planning_area_dict: Dict[int, PlanningArea],
                  station_dict: Dict[int, WeatherStation],
                  fire_centre_name: str,
                  jinja_env: Environment,
                  fuel_types: Dict[int, FuelType]):
    """Generates the prep cycle portion of the PDF"""
    prep_pdf_data, dates, date_range = response_2_prep_cycle_jinja_format(
        result,
        planning_area_dict,
        station_dict,
        fuel_types)
    template = jinja_env.get_template(PDFTemplateName.PREP.value)

    return template.render(
        idir=idir,
        datetime_generated=datetime_generated.isoformat(),
        planning_areas=prep_pdf_data,
        prep_days=dates,
        fire_centre_name=fire_centre_name,
        date_range=date_range)


def generate_daily(result: HFIResultResponse,
                   idir: str,
                   datetime_generated: datetime,
                   planning_area_dict: Dict[int, PlanningArea],
                   station_dict: Dict[int, WeatherStation],
                   fire_centre_name: str,
                   jinja_env: Environment,
                   fuel_types: Dict[int, FuelType]) -> str:
    """Generates the daily portion of the PDF"""
    template = jinja_env.get_template(PDFTemplateName.DAILY.value)
    daily_pdf_data_by_date = response_2_daily_jinja_format(
        result,
        planning_area_dict,
        station_dict,
        fuel_types)
    return template.render(
        idir=idir,
        datetime_generated=datetime_generated.isoformat(),
        daily_pdf_data_by_date=daily_pdf_data_by_date,
        fire_centre_name=fire_centre_name)


def build_mappings(fire_centres: List[FireCentre]):
    """ Marshall hydrated fire centres into dicts keyed by id """
    fire_centre_dict: Dict[int, FireCentre] = {}
    planning_area_dict: Dict[int, PlanningArea] = {}
    station_dict: Dict[int, WeatherStation] = {}
    for fire_centre in fire_centres:
        fire_centre_dict[fire_centre.id] = fire_centre
        for planning_area in fire_centre.planning_areas:
            planning_area_dict[planning_area.id] = planning_area
            for station in planning_area.stations:
                station_dict[station.code] = station
    return fire_centre_dict, planning_area_dict, station_dict


def get_pdf_filename(fire_centre_name: str, date_generated: date, idir: str) -> str:
    """ Returns the formatted pdf filename """
    return fire_centre_name.replace(" ", "") + \
        "_HFICalculator_" + \
        date_generated.isoformat() + \
        "_" + \
        idir.upper() + \
        ".pdf"
