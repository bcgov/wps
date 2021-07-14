""" Fire Behaviour Analysis Calculator Tool
"""
import math
from datetime import date
import logging
from app.utils.hfi_calculator import FUEL_TYPE_LOOKUP
from app.utils import cffdrs
from app.utils.time import get_hour_20_from_date, get_julian_date

logger = logging.getLogger(__name__)


class CannotCalculateFireTypeError(Exception):
    """ Exception thrown when fire type cannot be established """


class FBACalculatorWeatherStation():  # pylint: disable=too-many-instance-attributes
    """ Inputs for Fire Behaviour Advisory Calculator """

    def __init__(self,  # pylint: disable=too-many-arguments
                 elevation: int, fuel_type: str,
                 time_of_interest: date, percentage_conifer: float,
                 percentage_dead_balsam_fir: float, grass_cure: float,
                 crown_base_height: int, lat: float, long: float, bui: float, ffmc: float, isi: float,
                 wind_speed: float):
        self.elevation = elevation
        self.fuel_type = fuel_type
        self.time_of_interest = time_of_interest
        self.percentage_conifer = percentage_conifer
        self.percentage_dead_balsam_fir = percentage_dead_balsam_fir
        self.grass_cure = grass_cure
        self.crown_base_height = crown_base_height
        self.lat = lat
        self.long = long
        self.bui = bui
        self.ffmc = ffmc
        self.isi = isi
        self.wind_speed = wind_speed


class FireBehaviourAdvisory():  # pylint: disable=too-many-instance-attributes
    """ Class containing the results of the fire behaviour advisory calculation. """

    def __init__(self,  # pylint: disable=too-many-arguments
                 hfi: float, ros: float, fire_type: str, cfb: float, flame_length: float,
                 sixty_minute_fire_size: float, thirty_minute_fire_size: float, ffmc_for_hfi_4000: float,
                 hfi_when_ffmc_equals_ffmc_for_hfi_4000: float, ffmc_for_hfi_10000: float,
                 hfi_when_ffmc_equals_ffmc_for_hfi_10000: float):
        self.hfi = hfi
        self.ros = ros
        self.fire_type = fire_type  # TODO: make this an enum
        self.cfb = cfb
        self.flame_length = flame_length
        self.sixty_minute_fire_size = sixty_minute_fire_size
        self.thirty_minute_fire_size = thirty_minute_fire_size
        self.ffmc_for_hfi_4000 = ffmc_for_hfi_4000
        self.hfi_when_ffmc_equals_ffmc_for_hfi_4000 = hfi_when_ffmc_equals_ffmc_for_hfi_4000
        self.ffmc_for_hfi_10000 = ffmc_for_hfi_10000
        self.hfi_when_ffmc_equals_ffmc_for_hfi_10000 = hfi_when_ffmc_equals_ffmc_for_hfi_10000


def calculate_fire_behavour_advisory(station: FBACalculatorWeatherStation) -> FireBehaviourAdvisory:
    """ Transform from the raw daily json object returned by wf1, to our fba_calc.StationResponse object.
    """
    # time of interest will be the same for all stations
    time_of_interest = get_hour_20_from_date(station.time_of_interest)

    fmc = cffdrs.foliar_moisture_content(station.lat, station.long, station.elevation,
                                         get_julian_date(time_of_interest))
    sfc = cffdrs.surface_fuel_consumption(station.fuel_type, station.bui,
                                          station.ffmc, station.percentage_conifer)
    lb_ratio = cffdrs.length_to_breadth_ratio(station.fuel_type, station.wind_speed)
    ros = cffdrs.rate_of_spread(station.fuel_type, isi=station.isi, bui=station.bui, fmc=fmc, sfc=sfc,
                                pc=station.percentage_conifer,
                                cc=station.grass_cure,
                                pdf=station.percentage_dead_balsam_fir,
                                cbh=station.crown_base_height
                                )
    if station.fuel_type in ('D1', 'O1A', 'O1B', 'S1', 'S2', 'S3'):
        # These fuel types don't have a crown fraction burnt. But CFB is needed for other calculations,
        # so we go with 0.
        cfb = 0
    elif station.crown_base_height is None:
        # We can't calculate cfb without a crown base height!
        cfb = None
    else:
        cfb = cffdrs.crown_fraction_burned(station.fuel_type, fmc=fmc, sfc=sfc,
                                           ros=ros, cbh=station.crown_base_height)

    cfl = FUEL_TYPE_LOOKUP[station.fuel_type].get('CFL', None)

    hfi = cffdrs.head_fire_intensity(fuel_type=station.fuel_type,
                                     percentage_conifer=station.percentage_conifer,
                                     percentage_dead_balsam_fir=station.percentage_dead_balsam_fir,
                                     bui=station.bui, ffmc=station.ffmc, ros=ros, cfb=cfb, cfl=cfl, sfc=sfc)

    ffmc_for_hfi_4000, hfi_when_ffmc_equals_ffmc_for_hfi_4000 = cffdrs.get_ffmc_for_target_hfi(
        station.fuel_type, station.percentage_conifer,
        station.percentage_dead_balsam_fir,
        station.bui, station.ffmc, ros, cfb, cfl, 4000)
    ffmc_for_hfi_10000, hfi_when_ffmc_equals_ffmc_for_hfi_10000 = cffdrs.get_ffmc_for_target_hfi(
        station.fuel_type, station.percentage_conifer,
        station.percentage_dead_balsam_fir, station.bui,
        station.ffmc, ros, cfb, cfl, target_hfi=10000)

    fire_type = get_fire_type(fuel_type=station.fuel_type, crown_fraction_burned=cfb)
    flame_length = get_approx_flame_length(hfi)
    sixty_minute_fire_size = get_60_minutes_fire_size(lb_ratio, ros)
    thirty_minute_fire_size = get_30_minutes_fire_size(lb_ratio, ros)

    return FireBehaviourAdvisory(
        hfi=hfi, ros=ros, fire_type=fire_type, cfb=cfb, flame_length=flame_length,
        sixty_minute_fire_size=sixty_minute_fire_size,
        thirty_minute_fire_size=thirty_minute_fire_size,
        ffmc_for_hfi_4000=ffmc_for_hfi_4000,
        hfi_when_ffmc_equals_ffmc_for_hfi_4000=hfi_when_ffmc_equals_ffmc_for_hfi_4000,
        ffmc_for_hfi_10000=ffmc_for_hfi_10000,
        hfi_when_ffmc_equals_ffmc_for_hfi_10000=hfi_when_ffmc_equals_ffmc_for_hfi_10000)


def get_30_minutes_fire_size(length_breadth_ratio: float, rate_of_spread: float):
    """ Returns estimated fire size in hectares after 30 minutes, based on LB ratio and ROS.
    Formula derived from sample HFI workbook (see HFI_spreadsheet.md).

    30 min fire size = (pi * spread^2) / (40,000 * LB ratio)
    where spread = 30 * ROS
    """
    return (math.pi * math.pow(30 * rate_of_spread, 2)) / (40000 * length_breadth_ratio)


def get_60_minutes_fire_size(length_breadth_ratio: float, rate_of_spread: float):
    """ Returns estimated fire size in hectares after 60 minutes, based on LB ratio and ROS.
    Formula derived from sample HFI workbook (see HFI_spreadsheet.md)

    60 min fire size = (pi * spread^2) / (40,000 * LB ratio)
    where spread = 60 * ROS
    """
    return (math.pi * math.pow(60 * rate_of_spread, 2)) / (40000 * length_breadth_ratio)


def get_fire_type(fuel_type: str, crown_fraction_burned: float):
    """ Returns Fire Type (as str) based on percentage Crown Fraction Burned (CFB).
    These definitions come from the Red Book (p.69).
    Abbreviations for fire types have been taken from the red book (p.9).

    CROWN FRACTION BURNED           TYPE OF FIRE                ABBREV.
    < 10%                           Surface fire                S
    10-89%                          Intermittent crown fire     IC
    > 90%                           Continuous crown fire       CC

    # TODO: make this return an enum
    """
    if fuel_type == 'D1':
        # From red book "crown fires are not expected in deciduous fuel types but high intensity surface fires
        # can occur."
        return 'S'
    # crown fraction burnt is a floating point number from 0 to 1 inclusive.
    if crown_fraction_burned < 0.1:
        return 'S'
    if crown_fraction_burned < 0.9:
        return 'IC'
    if crown_fraction_burned >= 0.9:
        return 'CC'
    logger.error('Cannot calculate fire type. Invalid Crown Fraction Burned percentage received.')
    raise CannotCalculateFireTypeError


def get_approx_flame_length(head_fire_intensity: float):
    """ Returns an approximation of flame length (in meters).
    Formula used is a field-use approximation of
    L = (I / 300)^(1/2), where L is flame length in m and I is Fire Intensity in kW/m
    """
    return math.sqrt(head_fire_intensity / 300)
