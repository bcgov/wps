""" This module contains functions for computing fire weather metrics.
"""
import datetime
import logging
import app.utils.r_importer
from app.utils.singleton import Singleton
from app.utils.time import get_julian_date, get_julian_date_now
from app.wildfire_one.schema_parsers import WFWXWeatherStation


logger = logging.getLogger(__name__)


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

# PC, PDF, CC, CDH from the Red Book. Assumes values of 1 CBH.
# CC: Assume values of None for non grass types, and 0 for O1A and O1B.
# TODO: Store then in the DB as columns in FuelType
FUEL_TYPE_LOOKUP = {"C1": {"PC": 100, "PDF": 0, "CC": None, "CBH": 2},
                    "C2": {"PC": 100, "PDF": 0, "CC": None, "CBH": 3},
                    "C3": {"PC": 100, "PDF": 0, "CC": None, "CBH": 8},
                    "C4": {"PC": 100, "PDF": 0, "CC": None, "CBH": 4},
                    "C5": {"PC": 100, "PDF": 0, "CC": None, "CBH": 18},
                    # There's a 2m and 7m C6 in RB. Opted for 7m.
                    "C6": {"PC": 100, "PDF": 0, "CC": None, "CBH": 7},
                    "C7": {"PC": 100, "PDF": 0, "CC": None, "CBH": 10},
                    # No CBH listed in RB fire intensity class table for D1.
                    "D1": {"PC": 0, "PDF": 0, "CC": None, "CBH": 1},
                    # No CBH listed in RB fire intensity class table for D2.
                    "D2": {"PC": 0, "PDF": 0, "CC": None, "CBH": 1},
                    # 3 different PC configurations for M1. Opted for 50%.
                    "M1": {"PC": 50, "PDF": 0, "CC": None, "CBH": 6},
                    # 3 different PC configurations for M2. Opted for 50%.
                    "M2": {"PC": 50, "PDF": 0, "CC": None, "CBH": 6},
                    # 3 different PDF configurations for M3. Opted for 60%.
                    "M3": {"PC": 0, "PDF": 60, "CC": None, "CBH": 6},
                    # 3 different PDF configurations for M4. Opted for 60%.
                    "M4": {"PC": 0, "PDF": 60, "CC": None, "CBH": 6},
                    "O1A": {"PC": 0, "PDF": 0, "CC": 0, "CBH": 1},
                    "O1B": {"PC": 0, "PDF": 0, "CC": 0, "CBH": 1},
                    "S1": {"PC": 0, "PDF": 0, "CC": None, "CBH": 1},
                    "S2": {"PC": 0, "PDF": 0, "CC": None, "CBH": 1},
                    "S3": {"PC": 0, "PDF": 0, "CC": None, "CBH": 1}
                    }


def rate_of_spread(fuel_type: str, isi: float, bui: float, fmc: float, sfc: float):
    """ Computes ROS by delegating to cffdrs R package """
    if fuel_type is None or isi is None or bui is None or sfc is None:
        message = PARAMS_ERROR_MESSAGE + \
            "fuel_type: {fuel_type}, isi: {isi}, bui: {bui}, fmc: {fmc}, sfc: {sfc}"
        raise CFFDRSException(message)
    # pylint: disable=protected-access, no-member, line-too-long
    result = CFFDRS.instance().cffdrs._ROScalc(FUELTYPE=fuel_type, ISI=isi, BUI=bui, FMC=fmc, SFC=sfc,
                                               PC=FUEL_TYPE_LOOKUP[fuel_type]["PC"],
                                               PDF=FUEL_TYPE_LOOKUP[fuel_type]["PDF"],
                                               CC=FUEL_TYPE_LOOKUP[fuel_type]["CC"],
                                               CBH=FUEL_TYPE_LOOKUP[fuel_type]["CBH"])
    return result[0]

# Args:
#   FUELTYPE: The Fire Behaviour Prediction FuelType
#        BUI: Buildup Index
#       FFMC: Fine Fuel Moisture Code
#         PC: Percent Conifer (%)
#        GFL: Grass Fuel Load (kg/m^2) (3.5 kg/m^2)
# Returns:
#        SFC: Surface Fuel Consumption (kg/m^2)


def surface_fuel_consumption(fuel_type: str, bui: float, ffmc: float):
    """ Computes SFC by delegating to cffdrs R package
        Assumes a standard GFL of 3.5 kg/m ^ 2.
        NOTE: according to cffdrs R documentation, the default value for GFL is 0.35 kg/m^2, not 3.5
    """
    if fuel_type is None or bui is None or ffmc is None:
        message = PARAMS_ERROR_MESSAGE + \
            "fuel_type: {fuel_type}, bui: {bui}, ffmc: {ffmc}"
        raise CFFDRSException(message)
    # pylint: disable=protected-access, no-member, line-too-long
    result = CFFDRS.instance().cffdrs._SFCcalc(FUELTYPE=fuel_type, BUI=bui, FFMC=ffmc, PC=1, GFL=3.5)
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


def crown_fraction_burned(fuel_type: str, fmc: float, sfc: float, ros: float):
    """ Computes Crown Fraction Burned (CFB) by delegating to cffdrs R package.
    Value returned will be between 0-1.
    """
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._CFBcalc(FUELTYPE=fuel_type, FMC=fmc, SFC=sfc,
                                               ROS=ros, CBH=FUEL_TYPE_LOOKUP[fuel_type]["CBH"], option="CFB")
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


def total_fuel_consumption(fuel_type: str, cfb: float, sfc: float):
    """ Computes Total Fuel Consumption (TFC), which is a required input to calculate Head Fire Intensity.
    TFC is calculated by delegating to cffdrs R package.
    """
    # According to fbp.Rd in cffdrs R package, Crown Fuel Load (CFL) can use default value of 1.0
    # without causing major impacts on final output.
    cfl = 1.0
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._TFCcalc(FUELTYPE=fuel_type, CFL=cfl, CFB=cfb, SFC=sfc,
                                               PC=FUEL_TYPE_LOOKUP[fuel_type]["PC"], PDF=FUEL_TYPE_LOOKUP[fuel_type]["PDF"], option="TFC")
    return result[0]


def head_fire_intensity(station: WFWXWeatherStation, fuel_type: str, bui: float, ffmc: float, isi: float, time_of_interest: datetime):
    """ Computes Head Fire Intensity (HFI) by delegating to cffdrs R package.
    Calculating HFI requires a number of inputs that must be calculated first. This function
    first makes method calls to calculate the necessary intermediary values.
    """
    sfc = surface_fuel_consumption(fuel_type, bui, ffmc)
    fmc = foliar_moisture_content(station.lat, station.long, station.elevation,
                                  get_julian_date(time_of_interest))
    ros = rate_of_spread(fuel_type, isi, bui, fmc, sfc)
    cfb = crown_fraction_burned(fuel_type, fmc, sfc, ros)
    tfc = total_fuel_consumption(fuel_type, cfb, sfc)
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._FIcalc(FC=tfc, ROS=ros)
    return result[0]
