""" This module contains functions for computing fire weather metrics.
"""
import logging
from rpy2.robjects.packages import importr
cffdrs = importr('cffdrs')

logger = logging.getLogger(__name__)

#   From cffdrs R package comments:
#   FUELTYPE: The Fire Behaviour Prediction FuelType
#        ISI: Initial Spread Index
#        BUI: Buildup Index
#        FMC: Foliar Moisture Content
#        SFC: Surface Fuel Consumption (kg/m^2)
#         PC: Percent Conifer (%)
#        PDF: Percent Dead Balsam Fir (%)
#         CC: Constant (crown closure)
#        CBH: Crown to base height(m)

# Returns:
#   ROS: Rate of spread (m/min)
#

# Computable: SFC, FMC
# To store in DB: PC, PDF, CC, CBH (attached to fuel type, red book)
PARAMS_ERROR_MESSAGE = "One or more params passed to R call is None."

DEFAULT_METRICS = {"PC": 1, "PDF": 1, "CC": 1, "CBH": 1}

# TODO: Once PC, PDF, CC, CDH are confirmed, replace these defaults
# and potentially store then in the DB as columns in FuelType
FUEL_TYPE_LOOKUP = {"C1": DEFAULT_METRICS,
                    "C2": DEFAULT_METRICS,
                    "C3": DEFAULT_METRICS,
                    "C4": DEFAULT_METRICS,
                    "C5": DEFAULT_METRICS,
                    "C6": DEFAULT_METRICS,
                    "C7": DEFAULT_METRICS,
                    "D1": DEFAULT_METRICS,
                    "D2": DEFAULT_METRICS,
                    "M1": DEFAULT_METRICS,
                    "M2": DEFAULT_METRICS,
                    "M3": DEFAULT_METRICS,
                    "M4": DEFAULT_METRICS,
                    "O1A": DEFAULT_METRICS,
                    "O1B": DEFAULT_METRICS,
                    "S1": DEFAULT_METRICS,
                    "S2": DEFAULT_METRICS,
                    "S3": DEFAULT_METRICS
                    }


def rate_of_spread(fuel_type: str, isi: float, bui: float, fmc: float, sfc: float):
    """ Computes ROS by delegating to cffdrs R package """
    if fuel_type is None or isi is None or bui is None or sfc is None:
        logger.error(
            "%s fuel_type: %s. isi: %s, bui: %s, sfc: %s",
            PARAMS_ERROR_MESSAGE, fuel_type, isi, bui, sfc)
        return None
    # pylint: disable=protected-access, no-member, line-too-long
    result = cffdrs._ROScalc(FUELTYPE=fuel_type, ISI=isi, BUI=bui, FMC=fmc, SFC=sfc,
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
        Assumes a standard GFL of 3.5 kg/m^2.
    """
    if ffmc is None:
        logger.error(
            "%s fuel_type: %s. bui: %s, ffmc: %s",
            PARAMS_ERROR_MESSAGE, fuel_type, bui, ffmc)
        return None
    # pylint: disable=protected-access, no-member, line-too-long
    result = cffdrs._SFCcalc(FUELTYPE=fuel_type, BUI=bui, FFMC=ffmc, PC=1, GFL=3.5)
    return result[0]

  # Args:
  #   LAT:    Latitude (decimal degrees)
  #   LONG:   Longitude (decimal degrees)
  #   ELV:    Elevation (metres)
  #   DJ:     Day of year (offeren referred to as julian date)
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
    result = cffdrs._FMCcalc(LAT=lat, LONG=long, ELV=elv, DJ=day_of_year, D0=1)
    return result[0]
