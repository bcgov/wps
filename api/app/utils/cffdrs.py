""" This module contains functions for computing fire weather metrics.
"""
from rpy2.robjects.packages import importr
cffdrs = importr('cffdrs')

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


def rate_of_spread(fuel_type: str, isi: float, bui: float):
    """ Computes ROS by delegating to cffdrs R package """
    if fuel_type is None or isi is None or bui is None:
        return None
    # pylint: disable=protected-access, no-member, line-too-long
    result = cffdrs._ROScalc(FUELTYPE=fuel_type, ISI=isi, BUI=bui, CBH=6, SFC=1.5, PC=2, PDF=1, CC=1)
    return result[0]

# Args:
#   FUELTYPE: The Fire Behaviour Prediction FuelType
#        BUI: Buildup Index
#       FFMC: Fine Fuel Moisture Code
#         PC: Percent Conifer (%)
#        GFL: Grass Fuel Load (kg/m^2) (3.5 kg/m^2)
# Returns:
#        SFC: Surface Fuel Consumption (kg/m^2)


def surface_fuel_consumption(fuel_type: str, bui: float, ffmc: float, p_c: float, gfl: float):
    """ Computes SFC by delegating to cffdrs R package """
    print(fuel_type)
    print(bui)
    print(ffmc)
    print(p_c)
    print(gfl)

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


def fuel_moisture_content(lat: int, long: int, elv: float, day_of_year: int, minimum_fmc_date: float):
    """ Computes FMC by delegating to cffdrs R package """
    print(lat)
    print(long)
    print(elv)
    print(day_of_year)
    print(minimum_fmc_date)
