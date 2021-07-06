import math
from datetime import date
import logging

logger = logging.getLogger(__name__)


class FBACalculatorWeatherStation():
    """ A combination of station data from WFWX API and user-specified inputs for
    Fire Behaviour Advisory Calculator """

    def __init__(self, wfwx_id: str, code: int, elevation: int, fuel_type: str,
                 time_of_interest: date, percentage_conifer: float,
                 percentage_dead_balsam_fir: float, grass_cure: float,
                 crown_base_height: int, lat: float, long: float, name: str):
        self.wfwx_id = wfwx_id
        self.code = code
        self.name = name
        self.elevation = elevation
        self.fuel_type = fuel_type
        self.time_of_interest = time_of_interest
        self.percentage_conifer = percentage_conifer
        self.percentage_dead_balsam_fir = percentage_dead_balsam_fir
        self.grass_cure = grass_cure
        self.crown_base_height = crown_base_height
        self.lat = lat
        self.long = long


def get_30_minutes_fire_size(length_breadth_ratio: float, rate_of_spread: float):
    """ Returns estimated fire size in hectares after 30 minutes, based on LB ratio and ROS.
    Formula derived from sample HFI workbook (see HFI_spreadsheet.md).

    30 min fire size = (pi * spread^2) / (40,000 * LB ratio)
    where spread = 30 * ROS
    """
    size_in_square_meters = (math.pi * math.pow(30 * rate_of_spread, 2)) / (40000 * length_breadth_ratio)
    size_in_hectares = size_in_square_meters / 10000
    return size_in_hectares


def get_60_minutes_fire_size(length_breadth_ratio: float, rate_of_spread: float):
    """ Returns estimated fire size in hectares after 60 minutes, based on LB ratio and ROS.
    Formula derived from sample HFI workbook (see HFI_spreadsheet.md)

    60 min fire size = (pi * spread^2) / (40,000 * LB ratio)
    where spread = 60 * ROS
    """
    size_in_square_meters = (math.pi * math.pow(60 * rate_of_spread, 2)) / (40000 * length_breadth_ratio)
    size_in_hectares = size_in_square_meters / 10000
    return size_in_hectares


def get_fire_type(crown_fraction_burned: int):
    """ Returns Fire Type (as str) based on percentage Crown Fraction Burned (CFB).
    These definitions come from the Red Book (p.69).
    Abbreviations for fire types have been taken from the red book (p.9).

    CROWN FRACTION BURNED           TYPE OF FIRE                ABBREV.
    < 10%                           Surface fire                S
    10-89%                          Intermittent crown fire     IC
    > 90%                           Continuous crown fire       CC
    """
    if crown_fraction_burned < 10:
        return 'S'
    elif crown_fraction_burned < 90:
        return 'IC'
    elif crown_fraction_burned >= 90:
        return 'CC'
    else:
        logger.error('Cannot calculate fire type. Invalid Crown Fraction Burned percentage received.')
        raise Exception


def get_approx_flame_length(head_fire_intensity: float):
    """ Returns an approximation of flame length (in meters).
    Formula used is a field-use approximation of
    L = (I / 300)^(1/2), where L is flame length in m and I is Fire Intensity in kW/m
    """
    return math.sqrt(head_fire_intensity / 300)


def get_wind_speed_for_hfi_4000(station: FBACalculatorWeatherStation, bui: float, ffmc: float, isi: float, ros: float):
    """ Returns a floating point value for minimum wind speed (in km/h) required (holding all other
    values constant) before HFI reaches 4000 kW/m.
    """
    return 0.0


def get_ffmc_for_hfi_4000():
    """ Returns a floating point value for minimum FFMC required (holding all other values constant)
    before HFI reaches 4000 kW/m.
    """

    return 0.0


def get_wind_speed_for_hfi_10000():
    """ Returns a floating point value for minimum wind speed (in km/h) required (holding all other
    values constant) before HFI reaches 10,000 kW/m. """
    return 0.0


def get_ffmc_for_hfi_10000():
    """ Returns a floating point value for minimum FFMC required (holding all other values constant)
    before HFI reaches 10,000 kW/m. """
    return 0.0
