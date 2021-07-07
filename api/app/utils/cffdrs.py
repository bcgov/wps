""" This module contains functions for computing fire weather metrics.
"""
import logging
import rpy2.robjects as robjs
import rpy2.robjects.conversion as cv
from rpy2.rinterface import NULL
from app.utils.fba_calculator import FBACalculatorWeatherStation
import app.utils.r_importer
from app.utils.singleton import Singleton


logger = logging.getLogger(__name__)


def _none2null(_):
    """ Turn None values into null """
    return robjs.r("NULL")


none_converter = cv.Converter("None converter")
none_converter.py2rpy.register(type(None), _none2null)


@Singleton
class CFFDRS():
    """ Singleton that loads CFFDRS R lib once in memory for reuse."""

    def __init__(self):
        # pylint: disable=too-many-function-args
        self.cffdrs = app.utils.r_importer.import_cffsdrs()


class CFFDRSException(Exception):
    """ CFFDRS contextual exception """

#   From cffdrs R package comments:
#   FUELTYPE: The Fire Behaviour Prediction FuelType
#        ISI: Initial Spread Index
#        BUI: Buildup Index
#        FMC: Foliar Moisture Content
#        SFC: Surface Fuel Consumption (kg/m^2)
#         PC: Percent Conifer (%)
#        PDF: Percent Dead Balsam Fir (%)
#         CC: Constant (we think this is grass cure.)
#        CBH: Crown to base height(m)

# Returns:
#   ROS: Rate of spread (m/min)
#


# Computable: SFC, FMC
# To store in DB: PC, PDF, CC, CBH (attached to fuel type, red book)
PARAMS_ERROR_MESSAGE = "One or more params passed to R call is None."


def rate_of_spread(fuel_type: str,  # pylint: disable=too-many-arguments, disable=invalid-name
                   isi: float,
                   bui: float,
                   fmc: float,
                   sfc: float,
                   pc: float,
                   cc: float,
                   pdf: float,
                   cbh: float):
    """ Computes ROS by delegating to cffdrs R package.
    pdf: Percent Dead Balsam Fir (%)
    """
    if fuel_type is None or isi is None or bui is None or sfc is None:
        message = PARAMS_ERROR_MESSAGE + \
            "fuel_type: {fuel_type}, isi: {isi}, bui: {bui}, fmc: {fmc}, sfc: {sfc}".format(
                fuel_type=fuel_type, isi=isi, bui=bui, fmc=fmc, sfc=sfc)
        raise CFFDRSException(message)

    logger.info('calling _ROScalc(FUELTYPE=%s, ISI=%s, BUI=%s, FMC=%s, SFC=%s, PC=%s, PDF=%s, CC=%s, CBH=%s)',
                fuel_type, isi, bui, fmc, sfc, pc, pdf, cc, cbh)

    # For some reason, the registered converter can't turn a None to a NULL, but we need to
    # set these to NULL, despite setting a converter for None to NULL, because it it can only
    # convert a NULL to NULL. Doesn't make sense? Exactly.
    if pc is None:
        pc = NULL
    if cc is None:
        cc = NULL
    if pdf is None:
        pdf = NULL
    if cbh is None:
        cbh = NULL
    # pylint: disable=protected-access, no-member, line-too-long
    result = CFFDRS.instance().cffdrs._ROScalc(FUELTYPE=fuel_type,
                                               ISI=isi,
                                               BUI=bui,
                                               FMC=fmc,
                                               SFC=sfc,
                                               PC=pc,
                                               PDF=pdf,
                                               CC=cc,
                                               CBH=cbh)
    return result[0]

# Args:
#   FUELTYPE: The Fire Behaviour Prediction FuelType
#        BUI: Buildup Index
#       FFMC: Fine Fuel Moisture Code
#         PC: Percent Conifer (%)
#        GFL: Grass Fuel Load (kg/m^2) (3.5 kg/m^2)
# Returns:
#        SFC: Surface Fuel Consumption (kg/m^2)


def surface_fuel_consumption(  # pylint: disable=invalid-name
        fuel_type: str,
        bui: float,
        ffmc: float,
        pc: float):
    """ Computes SFC by delegating to cffdrs R package
        Assumes a standard GFL of 3.5 kg/m ^ 2.
        NOTE: according to cffdrs R documentation, the default value for GFL is 0.35 kg/m^2, not 3.5
    """
    if fuel_type is None or bui is None or ffmc is None:
        message = PARAMS_ERROR_MESSAGE + \
            "fuel_type: {fuel_type}, bui: {bui}, ffmc: {ffmc}".format(fuel_type=fuel_type, bui=bui, ffmc=ffmc)
        raise CFFDRSException(message)
    if pc is None:
        pc = NULL
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._SFCcalc(FUELTYPE=fuel_type,
                                               BUI=bui,
                                               FFMC=ffmc,
                                               PC=pc,
                                               GFL=3.5)
    return result[0]

    # Args:
    #   LAT:    Latitude (decimal degrees)
    #   LONG:   Longitude (decimal degrees)
    #   ELV:    Elevation (metres)
    #   DJ:     Day of year (often referred to as julian date)
    #   D0:     Date of minimum foliar moisture content
    #           (constant date, set by geography across province, 5 different dates)
    #
    # Returns:
    #   FMC:    Foliar Moisture Content


def foliar_moisture_content(lat: int, long: int, elv: float, day_of_year: int):
    """ Computes FMC by delegating to cffdrs R package
        TODO: Find out the minimum fmc date that is passed as D0, for now it's 1.
     """
    # pylint: disable=protected-access, no-member, line-too-long
    result = CFFDRS.instance().cffdrs._FMCcalc(LAT=lat, LONG=long, ELV=elv, DJ=day_of_year, D0=1)
    return result[0]

    # Args:
    #   FUELTYPE: The Fire Behaviour Prediction FuelType
    #        WSV: The Wind Speed (km/h)
    # Returns:
    #   LB: Length to Breadth ratio


def length_to_breadth_ratio(fuel_type: str, wind_speed: float):
    """ Computes L/B ratio by delegating to cffdrs R package """
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._LBcalc(FUELTYPE=fuel_type, WSV=wind_speed)
    return result[0]

    # Args:
    #   FUELTYPE: The Fire Behaviour Prediction FuelType
    #   FMC:      Foliar Moisture Content
    #   SFC:      Surface Fuel Consumption
    #   CBH:      Crown Base Height
    #   ROS:      Rate of Spread
    #   option:   Which variable to calculate(ROS, CFB, RSC, or RSI)

    # Returns:
    #   CFB, CSI, RSO depending on which option was selected.


def crown_fraction_burned(fuel_type: str, fmc: float, sfc: float, ros: float, cbh: float):
    """ Computes Crown Fraction Burned (CFB) by delegating to cffdrs R package.
    Value returned will be between 0-1.
    """
    # pylint: disable=protected-access, no-member
    if cbh is None:
        cbh = NULL
    if cbh is None or fmc is None:
        message = PARAMS_ERROR_MESSAGE + \
            "fuel_type: {fuel_type}, cbh: {cbh}, fmc: {fmc}".format(fuel_type=fuel_type, cbh=cbh, fmc=fmc)
        raise CFFDRSException(message)
    result = CFFDRS.instance().cffdrs._CFBcalc(FUELTYPE=fuel_type, FMC=fmc, SFC=sfc,
                                               ROS=ros, CBH=cbh)
    return result[0]

    # Args:
    #   FUELTYPE: The Fire Behaviour Prediction FuelType
    #        CFL: Crown Fuel Load (kg/m^2)
    #        CFB: Crown Fraction Burned (0-1)
    #        SFC: Surface Fuel Consumption (kg/m^2)
    #         PC: Percent Conifer (%)
    #        PDF: Percent Dead Balsam Fir (%)
    #     option: Type of output (TFC, CFC, default=TFC)
    # Returns:
    #        TFC: Total (Surface + Crown) Fuel Consumption (kg/m^2)
    #       OR
    #        CFC: Crown Fuel Consumption (kg/m^2)


def total_fuel_consumption(  # pylint: disable=invalid-name
        fuel_type: str, cfb: float, sfc: float, pc: float, pdf: float):
    """ Computes Total Fuel Consumption (TFC), which is a required input to calculate Head Fire Intensity.
    TFC is calculated by delegating to cffdrs R package.
    """
    if cfb is None:
        message = PARAMS_ERROR_MESSAGE + \
            "fuel_type: {fuel_type}, cfb: {cfb}".format(fuel_type=fuel_type, cfb=cfb)
        raise CFFDRSException(message)
    # According to fbp.Rd in cffdrs R package, Crown Fuel Load (CFL) can use default value of 1.0
    # without causing major impacts on final output.
    cfl = 1.0
    if pc is None:
        pc = NULL
    if pdf is None:
        pdf = NULL
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._TFCcalc(FUELTYPE=fuel_type, CFL=cfl, CFB=cfb, SFC=sfc,
                                               PC=pc,
                                               PDF=pdf)
    return result[0]


def head_fire_intensity(
        station: FBACalculatorWeatherStation, bui: float, ffmc: float, ros: float, cfb: float):
    """ Computes Head Fire Intensity (HFI) by delegating to cffdrs R package.
    Calculating HFI requires a number of inputs that must be calculated first. This function
    first makes method calls to calculate the necessary intermediary values.
    """
    sfc = surface_fuel_consumption(station.fuel_type, bui, ffmc, station.percentage_conifer)
    tfc = total_fuel_consumption(station.fuel_type, cfb, sfc,
                                 station.percentage_conifer, station.percentage_dead_balsam_fir)
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._FIcalc(FC=tfc, ROS=ros)
    return result[0]
