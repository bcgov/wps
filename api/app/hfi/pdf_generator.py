"""Generate a daily PDF"""
import logging
from datetime import date, datetime
from typing import List, Dict, Tuple
import pdfkit
from jinja2 import Environment
from app.schemas.hfi_calc import FireCentre, HFIResultResponse, PlanningArea, StationInfo, WeatherStation
from app.hfi.pdf_template import PDFTemplateName, CSS_PATH
from app.hfi.pdf_data_formatter import response_2_daily_jinja_format, response_2_prep_cycle_jinja_format


logger = logging.getLogger(__name__)


def generate_html(result: HFIResultResponse,
                  fire_centres: List[FireCentre],
                  idir: str,
                  datetime_generated: datetime,
                  jinja_env: Environment,
                  fuel_types: Dict[int, StationInfo]) -> Tuple[str, str]:
    """Generates the full HTML based on the HFIResultResponse"""
    override_fuel_types(fire_centres, result, fuel_types)
    fire_centre_dict, planning_area_dict, station_dict = build_mappings(fire_centres)
    fire_centre_name = fire_centre_dict[result.selected_fire_center_id].name

    rendered_output = generate_prep(result,
                                    idir,
                                    datetime_generated,
                                    planning_area_dict,
                                    station_dict,
                                    fire_centre_name,
                                    jinja_env)
    rendered_output += generate_daily(result,
                                      idir,
                                      datetime_generated,
                                      planning_area_dict,
                                      station_dict,
                                      fire_centre_name,
                                      jinja_env)

    return rendered_output, fire_centre_name


def override_fuel_types(
        fire_centres: List[FireCentre],
        result: HFIResultResponse,
        fuel_types: Dict[int, StationInfo]):
    """ Override the fuel types in the fire centre with the fuel types from the result """
    fire_centre: FireCentre = next(
        fire_centre for fire_centre in fire_centres if fire_centre.id == result.selected_fire_center_id)
    for planning_area in fire_centre.planning_areas:
        station_info_list: List[StationInfo] = result.planning_area_station_info[planning_area.id]
        for station in planning_area.stations:
            try:
                station_info: StationInfo = next(
                    station_info for station_info in
                    station_info_list if station_info.station_code == station.code)
            except StopIteration:
                # This shouldn't happen, and we don't bother writing a test case to re-produce.
                logger.error('Could no find station info for station code %s in planning area %s',
                             station.code, planning_area.id)
                raise
            station.station_props.fuel_type = fuel_types[station_info.fuel_type_id]


def generate_pdf(result: HFIResultResponse,
                 fire_centres: List[FireCentre],
                 idir: str,
                 datetime_generated: datetime,
                 jinja_env: Environment,
                 fuel_types: Dict[int, StationInfo]) -> Tuple[bytes, str]:
    """Generates the full PDF based on the HFIResultResponse"""
    rendered_output, fire_centre_name = generate_html(result,
                                                      fire_centres,
                                                      idir,
                                                      datetime_generated,
                                                      jinja_env,
                                                      fuel_types)

    # pylint: disable=line-too-long
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
                  jinja_env: Environment):
    """Generates the prep cycle portion of the PDF"""
    prep_pdf_data, dates, date_range = response_2_prep_cycle_jinja_format(
        result,
        planning_area_dict,
        station_dict)
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
                   jinja_env: Environment) -> str:
    """Generates the daily portion of the PDF"""
    template = jinja_env.get_template(PDFTemplateName.DAILY.value)
    daily_pdf_data_by_date = response_2_daily_jinja_format(
        result,
        planning_area_dict,
        station_dict)
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
