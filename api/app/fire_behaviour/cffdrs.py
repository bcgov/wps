""" This module contains functions for computing fire weather metrics.
"""
import logging
import math
from typing import Optional
import rpy2
import rpy2.robjects as robjs
from rpy2.robjects import pandas2ri
from rpy2.rinterface import NULL
import pandas as pd
import app.utils.r_importer
from app.utils.singleton import Singleton
from wps_shared.fuel_types import FuelTypeEnum


logger = logging.getLogger(__name__)


def _none2null(_):
    """ Turn None values into null """
    return robjs.r("NULL")


none_converter = robjs.conversion.Converter("None converter")
none_converter.py2rpy.register(type(None), _none2null)


@Singleton
class CFFDRS():
    """ Singleton that loads CFFDRS R lib once in memory for reuse."""

    def __init__(self):
        self.cffdrs = app.utils.r_importer.import_cffsdrs()


class CFFDRSException(Exception):
    """ CFFDRS contextual exception """


# Computable: SFC, FMC
# To store in DB: PC, PDF, CC, CBH (attached to fuel type, red book)
PARAMS_ERROR_MESSAGE = "One or more params passed to R call is None."


def correct_wind_azimuth(wind_direction: float):
    """
    #Corrections to reorient Wind Azimuth(WAZ)
    WAZ <- WD + pi
    WAZ <- ifelse(WAZ > 2 * pi, WAZ - 2 * pi, WAZ)
    """
    if wind_direction is None:
        return None
    waz = wind_direction + math.pi
    if waz > 2 * math.pi:
        return waz - 2 * math.pi
    return waz


def calculate_wind_speed(fuel_type: FuelTypeEnum,
                         ffmc: float,
                         bui: float,
                         ws: float,
                         fmc: float,
                         sfc: float,
                         pc: float,
                         cc: float,
                         pdf: float,
                         cbh: float,
                         isi: float):
    """
     Wind azimuth, slope azimuth, ground slope, net effective windspeed
    """
    wind_azimuth = correct_wind_azimuth(ws)
    slope_azimuth = None  # a.k.a. SAZ
    ground_slope = 0  # right now we're not taking slope into account
    wsv = calculate_net_effective_windspeed(fuel_type=fuel_type,
                                            ffmc=ffmc,
                                            bui=bui,
                                            ws=ws,
                                            waz=wind_azimuth,
                                            gs=ground_slope,
                                            saz=slope_azimuth,
                                            fmc=fmc,
                                            sfc=sfc,
                                            pc=pc,
                                            cc=cc,
                                            pdf=pdf,
                                            cbh=cbh,
                                            isi=isi)
    return wsv


def calculate_net_effective_windspeed(fuel_type: FuelTypeEnum,
                                      ffmc: float,
                                      bui: float,
                                      ws: float,
                                      waz: float,
                                      gs: float,
                                      saz: Optional[float],
                                      fmc: float,
                                      sfc: float,
                                      pc: float,
                                      cc: float,
                                      pdf: float,
                                      cbh: float,
                                      isi: float):
    """
    #Calculate the net effective windspeed (WSV)
    WSV0 <- .Slopecalc(FUELTYPE, FFMC, BUI, WS, WAZ, GS, SAZ,
                        FMC, SFC, PC, PDF, CC, CBH, ISI, output = "WSV")
    WSV <- ifelse(GS > 0 & FFMC > 0, WSV0, WS)
    """
    if gs > 0 and ffmc > 0:
        # Description:
        #   Calculate the net effective windspeed (WSV), the net effective wind
        #   direction (RAZ) or the wind azimuth (WAZ).
        #
        #   All variables names are laid out in the same manner as FCFDG (1992) and
        #   Wotton (2009).
        #
        #
        #   Forestry Canada Fire Danger Group (FCFDG) (1992). "Development and
        #   Structure of the Canadian Forest Fire Behavior Prediction System."
        #   Technical Report ST-X-3, Forestry Canada, Ottawa, Ontario.
        #
        #   Wotton, B.M., Alexander, M.E., Taylor, S.W. 2009. Updates and revisions to
        #   the 1992 Canadian forest fire behavior prediction system. Nat. Resour.
        #   Can., Can. For. Serv., Great Lakes For. Cent., Sault Ste. Marie, Ontario,
        #   Canada. Information Report GLC-X-10, 45p.
        #
        # Args:
        #   FUELTYPE: The Fire Behaviour Prediction FuelType
        #       FFMC: Fine Fuel Moisture Code
        #        BUI: The Buildup Index value
        #         WS: Windspeed (km/h)
        #        WAZ: Wind Azimuth
        #         GS: Ground Slope (%)
        #        SAZ: Slope Azimuth
        #        FMC: Foliar Moisture Content
        #        SFC: Surface Fuel Consumption (kg/m^2)
        #         PC: Percent Conifer (%)
        #        PDF: Percent Dead Balsam Fir (%)
        #         CC: Constant
        #        CBH: Crown Base Height (m)
        #        ISI: Initial Spread Index
        #     output: Type of variable to output (RAZ/WSV, default=RAZ)
        # Returns:
        #   BE: The Buildup Effect
        result = CFFDRS.instance().cffdrs._Slopecalc(FUELTYPE=fuel_type.value,
                                                     FFMC=ffmc,
                                                     BUI=bui,
                                                     WS=ws,
                                                     WAZ=waz,
                                                     GS=gs,
                                                     SAZ=saz,
                                                     FMC=fmc,
                                                     SFC=sfc,
                                                     PC=pc,
                                                     PDF=pdf,
                                                     CC=cc,
                                                     CBH=cbh,
                                                     ISI=isi,
                                                     output="WSV")
        if isinstance(result[0], float):
            return result[0]
        raise CFFDRSException("Failed to calculate Slope")
    return ws


def flank_rate_of_spread(ros: float, bros: float, lb: float):
    """
    # Description:
    #   Calculate the Flank Fire Spread Rate.
    #
    #   All variables names are laid out in the same manner as Forestry Canada
    #   Fire Danger Group (FCFDG) (1992). Development and Structure of the
    #   Canadian Forest Fire Behavior Prediction System." Technical Report
    #   ST-X-3, Forestry Canada, Ottawa, Ontario.
    #
    # Args:
    #   ROS:    Fire Rate of Spread (m/min)
    #   BROS:   Back Fire Rate of Spread (m/min)
    #   LB:     Length to breadth ratio
    #

    # Returns:
    #   FROS:   Flank Fire Spread Rate (m/min)
    #
    """
    result = CFFDRS.instance().cffdrs._FROScalc(ROS=ros, BROS=bros, LB=lb)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate FROS")


def back_rate_of_spread(fuel_type: FuelTypeEnum,
                        ffmc: float,
                        bui: float,
                        wsv: float,
                        fmc: float,
                        sfc: float,
                        pc: float,
                        cc: float,
                        pdf: float,
                        cbh: float):
    """
    # Description:
    #   Calculate the Back Fire Spread Rate.
    #
    #   All variables names are laid out in the same manner as Forestry Canada
    #   Fire Danger Group (FCFDG) (1992). Development and Structure of the
    #   Canadian Forest Fire Behavior Prediction System." Technical Report
    #   ST-X-3, Forestry Canada, Ottawa, Ontario.
    #
    # Args:
    #   FUELTYPE: The Fire Behaviour Prediction FuelType
    #   FFMC:     Fine Fuel Moisture Code
    #   BUI:      Buildup Index
    #   WSV:      Wind Speed Vector
    #   FMC:      Foliar Moisture Content
    #   SFC:      Surface Fuel Consumption
    #   PC:       Percent Conifer
    #   PDF:      Percent Dead Balsam Fir
    #   CC:       Degree of Curing (just "C" in FCFDG 1992)
    #   CBH:      Crown Base Height

    # Returns:
    #   BROS:     Back Fire Spread Rate
    #
    """

    if fuel_type is None or ffmc is None or bui is None or fmc is None or sfc is None:
        message = PARAMS_ERROR_MESSAGE + \
            f"_BROScalc ; fuel_type: {fuel_type.value}, ffmc: {ffmc}, bui: {bui}, fmc: {fmc}, sfc: {sfc}"
        raise CFFDRSException(message)

    if pc is None:
        pc = NULL
    if cc is None:
        cc = NULL
    if pdf is None:
        pdf = NULL
    if cbh is None:
        cbh = NULL
    if wsv is None:
        wsv = NULL
    result = CFFDRS.instance().cffdrs._BROScalc(FUELTYPE=fuel_type.value,
                                                FFMC=ffmc,
                                                BUI=bui,
                                                WSV=wsv,
                                                FMC=fmc,
                                                SFC=sfc,
                                                PC=pc,
                                                PDF=pdf,
                                                CC=cc,
                                                CBH=cbh)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate BROS")


def bui_calc(dmc: float, dc: float):
    """
    # Description: Buildup Index Calculation. All code
    #              is based on a C code library that was written by Canadian
    #              Forest Service Employees, which was originally based on
    #              the Fortran code listed in the reference below. All equations
    #              in this code refer to that document.
    #
    #              Equations and FORTRAN program for the Canadian Forest Fire
    #              Weather Index System. 1985. Van Wagner, C.E.; Pickett, T.L.
    #              Canadian Forestry Service, Petawawa National Forestry
    #              Institute, Chalk River, Ontario. Forestry Technical Report 33.
    #              18 p.
    #
    #              Additional reference on FWI system
    #
    #              Development and structure of the Canadian Forest Fire Weather
    #              Index System. 1987. Van Wagner, C.E. Canadian Forestry Service,
    #              Headquarters, Ottawa. Forestry Technical Report 35. 35 p.
    #
    #
    # Args:   dc:   Drought Code
    #        dmc:   Duff Moisture Code
    #
    # Returns: A single bui value
    """
    result = CFFDRS.instance().cffdrs._buiCalc(dmc=dmc, dc=dc)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate bui")


def rate_of_spread_t(fuel_type: FuelTypeEnum,
                     ros_eq: float,
                     minutes_since_ignition: float,
                     cfb: float):
    """
    # Description:
    #   Computes the Rate of Spread prediction based on fuel type and FWI
    #   conditions at elapsed time since ignition. Equations are from listed
    #   FCFDG (1992).
    #
    #   All variables names are laid out in the same manner as Forestry Canada
    #   Fire Danger Group (FCFDG) (1992). Development and Structure of the
    #   Canadian Forest Fire Behavior Prediction System." Technical Report
    #   ST-X-3, Forestry Canada, Ottawa, Ontario.
    #
    # Args:
    #   FUELTYPE: The Fire Behaviour Prediction FuelType
    #      ROSeq: Equilibrium Rate of Spread (m/min)
    #         HR: Time since ignition (hours)
    #        CFB: Crown Fraction Burned
    # Returns:
    #   ROSt: Rate of Spread at time since ignition
    #
    """
    # NOTE: CFFDRS documentation incorrectly states that HR is hours since ignition, it's actually
    # minutes.
    result = CFFDRS.instance().cffdrs._ROStcalc(FUELTYPE=fuel_type.value,
                                                ROSeq=ros_eq,
                                                HR=minutes_since_ignition,
                                                CFB=cfb)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate ROSt")


def rate_of_spread(fuel_type: FuelTypeEnum,
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
    NOTE: For C1, only ISI and BUI is used to calculate ROS. All other inputs are ignored.
    """
    if fuel_type is None or isi is None or bui is None or sfc is None:
        message = PARAMS_ERROR_MESSAGE + \
            f"_ROScalc ; fuel_type: {fuel_type.value}, isi: {isi}, bui: {bui}, fmc: {fmc}, sfc: {sfc}"
        raise CFFDRSException(message)

    # For some reason, the registered converter can't turn a None to a NULL, but we need to
    # set these to NULL, despite setting a converter for None to NULL, because it it can only
    # convert a NULL to NULL. Doesn't make sense? Exactly.
    # https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.deviantart.com%2Ffirefox2014%2Fart%2FJackie-Chan-Meme-525778492&psig=AOvVaw3WsEdtu_OswdactmBuGmtH&ust=1625962534127000&source=images&cd=vfe&ved=0CAoQjRxqFwoTCNCc0dac1_ECFQAAAAAdAAAAABAD
    if pc is None:
        pc = NULL
    if cc is None:
        cc = NULL
    if pdf is None:
        pdf = NULL
    if cbh is None:
        cbh = NULL
    result = CFFDRS.instance().cffdrs._ROScalc(FUELTYPE=fuel_type.value,
                                               ISI=isi,
                                               BUI=bui,
                                               FMC=fmc,
                                               SFC=sfc,
                                               PC=pc,
                                               PDF=pdf,
                                               CC=cc,
                                               CBH=cbh)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate ROS")


def surface_fuel_consumption(
        fuel_type: FuelTypeEnum,
        bui: float,
        ffmc: float,
        pc: float):
    """ Computes SFC by delegating to cffdrs R package
        Assumes a standard GFL of 0.35 kg/m ^ 2.

    # Args:
    #   FUELTYPE: The Fire Behaviour Prediction FuelType
    #        BUI: Buildup Index
    #       FFMC: Fine Fuel Moisture Code
    #         PC: Percent Conifer (%)
    #        GFL: Grass Fuel Load (kg/m^2) (0.35 kg/m^2)
    # Returns:
    #        SFC: Surface Fuel Consumption (kg/m^2)
    """
    if fuel_type is None or bui is None or ffmc is None:
        message = PARAMS_ERROR_MESSAGE + \
            f"_SFCcalc; fuel_type: {fuel_type.value}, bui: {bui}, ffmc: {ffmc}"
        raise CFFDRSException(message)
    if pc is None:
        pc = NULL
    result = CFFDRS.instance().cffdrs._SFCcalc(FUELTYPE=fuel_type.value,
                                               BUI=bui,
                                               FFMC=ffmc,
                                               PC=pc,
                                               GFL=0.35)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate SFC")


def fire_distance(fuel_type: FuelTypeEnum, ros_eq: float, hr: int, cfb: float):
    """
    # Description:
    #   Calculate the Head fire spread distance at time t. In the documentation
    #   this variable is just "D".
    #
    #   All variables names are laid out in the same manner as Forestry Canada
    #   Fire Danger Group (FCFDG) (1992). Development and Structure of the
    #   Canadian Forest Fire Behavior Prediction System." Technical Report
    #   ST-X-3, Forestry Canada, Ottawa, Ontario.
    #
    # Args:
    #   FUELTYPE: The Fire Behaviour Prediction FuelType
    #   ROSeq:    The predicted equilibrium rate of spread (m/min)
    #   HR (t):   The elapsed time (min)
    #   CFB:      Crown Fraction Burned
    #
    # Returns:
    #   DISTt:    Head fire spread distance at time t
    """
    result = CFFDRS.instance().cffdrs._DISTtcalc(fuel_type.value, ros_eq, hr, cfb)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate DISTt")


def foliar_moisture_content(lat: int, long: int, elv: float, day_of_year: int,
                            date_of_minimum_foliar_moisture_content: int = 0):
    """ Computes FMC by delegating to cffdrs R package
        TODO: Find out the minimum fmc date that is passed as D0, for now it's 0. Passing 0 makes FFMCcalc
        calculate it.

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
     """
    logger.debug('calling _FMCcalc(LAT=%s, LONG=%s, ELV=%s, DJ=%s, D0=%s)', lat,
                 long, elv, day_of_year, date_of_minimum_foliar_moisture_content)
    # FMCcalc expects longitude to always be a positive number.
    if long < 0:
        long = -long
    result = CFFDRS.instance().cffdrs._FMCcalc(LAT=lat, LONG=long, ELV=elv,
                                               DJ=day_of_year, D0=date_of_minimum_foliar_moisture_content)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate FMC")


def length_to_breadth_ratio(fuel_type: FuelTypeEnum, wind_speed: float):
    """ Computes L/B ratio by delegating to cffdrs R package

    # Args:
    #   FUELTYPE: The Fire Behaviour Prediction FuelType
    #        WSV: The Wind Speed (km/h)
    # Returns:
    #   LB: Length to Breadth ratio
    """
    if wind_speed is None or fuel_type is None:
        return CFFDRSException()
    result = CFFDRS.instance().cffdrs._LBcalc(FUELTYPE=fuel_type.value, WSV=wind_speed)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate LB")


def length_to_breadth_ratio_t(fuel_type: FuelTypeEnum,
                              lb: float,
                              time_since_ignition: float,
                              cfb: float):
    """ Computes L/B ratio by delegating to cffdrs R package

    # Description:
    #   Computes the Length to Breadth ratio of an elliptically shaped fire at
    #   elapsed time since ignition. Equations are from listed FCFDG (1992) and
    #   Wotton et. al. (2009), and are marked as such.
    #
    #   All variables names are laid out in the same manner as Forestry Canada
    #   Fire Danger Group (FCFDG) (1992). Development and Structure of the
    #   Canadian Forest Fire Behavior Prediction System." Technical Report
    #   ST-X-3, Forestry Canada, Ottawa, Ontario.
    #
    #   Wotton, B.M., Alexander, M.E., Taylor, S.W. 2009. Updates and revisions to
    #   the 1992 Canadian forest fire behavior prediction system. Nat. Resour.
    #   Can., Can. For. Serv., Great Lakes For. Cent., Sault Ste. Marie, Ontario,
    #   Canada. Information Report GLC-X-10, 45p.
    #
    # Args:
    #   FUELTYPE: The Fire Behaviour Prediction FuelType
    #         LB: Length to Breadth ratio
    #         HR: Time since ignition (hours)
    #        CFB: Crown Fraction Burned
    # Returns:
    #   LBt: Length to Breadth ratio at time since ignition
    #
    """
    result = CFFDRS.instance().cffdrs._LBtcalc(FUELTYPE=fuel_type.value, LB=lb,
                                               HR=time_since_ignition, CFB=cfb)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate LBt")


def fine_fuel_moisture_code(ffmc: float, temperature: float, relative_humidity: float,
                            precipitation: float, wind_speed: float):
    """ Computes Fine Fuel Moisture Code (FFMC) by delegating to cffdrs R package.
    This is necessary when recalculating certain fire weather indices based on
    user-defined input for wind speed.

    # Args: ffmc_yda:   The Fine Fuel Moisture Code from previous iteration
    #           temp:   Temperature (centigrade)
    #             rh:   Relative Humidity (%)
    #           prec:   Precipitation (mm)
    #             ws:   Wind speed (km/h)
    #
    #
    # Returns: A single ffmc value
    """

    if ffmc is None:
        logger.error("Failed to calculate FFMC; initial FFMC is required.")
        return None
    if temperature is None:
        temperature = NULL
    if relative_humidity is None:
        relative_humidity = NULL
    if precipitation is None:
        precipitation = NULL
    if wind_speed is None:
        # _ffmcCalc with throw if passed a NULL windspeed, so log a message and return None.
        logger.error("Failed to calculate ffmc")
        return None
    result = CFFDRS.instance().cffdrs._ffmcCalc(ffmc_yda=ffmc, temp=temperature, rh=relative_humidity,
                                                prec=precipitation, ws=wind_speed)
    if len(result) == 0:
        logger.error("Failed to calculate ffmc")
        return None
    if isinstance(result[0], float):
        return result[0]
    
    logger.error("Failed to calculate ffmc")
    return None

def duff_moisture_code(dmc: float, temperature: float, relative_humidity: float,
                       precipitation: float, latitude: float = 55, month: int = 7,
                       latitude_adjust: bool = True):
    """
    Computes Duff Moisture Code (DMC) by delegating to the cffdrs R package.

    R function signature: 
    function (dmc_yda, temp, rh, prec, lat, mon, lat.adjust = TRUE)

    :param dmc: The Duff Moisture Code (unitless) of the previous day
    :type dmc: float
    :param temperature: Temperature (centigrade)
    :type temperature: float
    :param relative_humidity: Relative humidity (%)
    :type relative_humidity: float
    :param precipitation: 24-hour rainfall (mm)
    :type precipitation: float
    :param latitude: Latitude (decimal degrees), defaults to 55
    :type latitude: float
    :param month: Month of the year (1-12), defaults to 7 (July)
    :type month: int, optional
    :param latitude_adjust: Options for whether day length adjustments should be applied to 
    the calculation, defaults to True
    :type latitude_adjust: bool, optional
    """
    if dmc is None:
        logger.error("Failed to calculate DMC; initial DMC is required.")
        return None
    if temperature is None:
        temperature = NULL
    if relative_humidity is None:
        relative_humidity = NULL
    if precipitation is None:
        precipitation = NULL
    if latitude is None:
        latitude = 55
    if month is None:
        month = 7
    result = CFFDRS.instance().cffdrs._dmcCalc(dmc, temperature, relative_humidity, precipitation,
                                               latitude, month, latitude_adjust)

    if len(result) == 0:
        logger.error("Failed to calculate DMC")
        return None
    if isinstance(result[0], float):
        return result[0]
    logger.error("Failed to calculate DMC")
    return None


def drought_code(dc: float, temperature: float, relative_humidity: float, precipitation: float,
                 latitude: float = 55, month: int = 7, latitude_adjust: bool = True) -> None:
    """
    Computes Drought Code (DC) by delegating to the cffdrs R package.

    :param dc: The Drought Code (unitless) of the previous day
    :type dc: float
    :param temperature: Temperature (centigrade)
    :type temperature: float
    :param relative_humidity: Relative humidity (%)
    :type relative_humidity: float
    :param precipitation: 24-hour rainfall (mm)
    :type precipitation: float
    :param latitude: Latitude (decimal degrees), defaults to 55
    :type latitude: float
    :param month: Month of the year (1-12), defaults to 7 (July)
    :type month: int, optional
    :param latitude_adjust: Options for whether day length adjustments should be applied to 
    the calculation, defaults to True
    :type latitude_adjust: bool, optional
    :raises CFFDRSException:
    :return: None
    """
    if dc is None:
        logger.error("Failed to calculate DC; initial DC is required.")
        return None
    if temperature is None:
        temperature = NULL
    if relative_humidity is None:
        relative_humidity = NULL
    if precipitation is None:
        precipitation = NULL
    if latitude is None:
        latitude = 55
    if month is None:
        month = 7
    result = CFFDRS.instance().cffdrs._dcCalc(dc, temperature, relative_humidity, precipitation,
                                              latitude, month, latitude_adjust)
    if len(result) == 0:
        logger.error("Failed to calculate DC")
        return None
    if isinstance(result[0], float):
        return result[0]
    logger.error("Failed to calculate DC")
    return None


def initial_spread_index(ffmc: float, wind_speed: float, fbp_mod: bool = False):
    """ Computes Initial Spread Index (ISI) by delegating to cffdrs R package.
    This is necessary when recalculating ROS/HFI for modified FFMC values. Otherwise,
    should be using the ISI value retrieved from WFWX.

    # Args:
    #   ffmc:   Fine Fuel Moisture Code
    #     ws:   Wind Speed (km/h)
    # fbpMod:   TRUE/FALSE if using the fbp modification at the extreme end
    #
    # Returns:
    #   ISI:    Intial Spread Index
    """
    if ffmc is None:
        ffmc = NULL
    result = CFFDRS.instance().cffdrs._ISIcalc(ffmc=ffmc, ws=wind_speed, fbpMod=fbp_mod)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate ISI")


def fire_weather_index(isi: float, bui: float):
    """ Computes Fire Weather Index (FWI) by delegating to cffdrs R package.

        Args:   isi:    Initial Spread Index
                bui:    Buildup Index

        Returns: A single fwi value
    """

    result = CFFDRS.instance().cffdrs._fwiCalc(isi=isi, bui=bui)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate fwi")


def crown_fraction_burned(fuel_type: FuelTypeEnum, fmc: float, sfc: float,
                          ros: float, cbh: float) -> float:
    """ Computes Crown Fraction Burned (CFB) by delegating to cffdrs R package.
    Value returned will be between 0-1.

    # Args:
    #   FUELTYPE: The Fire Behaviour Prediction FuelType
    #   FMC:      Foliar Moisture Content
    #   SFC:      Surface Fuel Consumption
    #   CBH:      Crown Base Height
    #   ROS:      Rate of Spread
    #   option:   Which variable to calculate(ROS, CFB, RSC, or RSI)

    # Returns:
    #   CFB, CSI, RSO depending on which option was selected.
    """
    if cbh is None:
        cbh = NULL
    if cbh is None or fmc is None:
        message = PARAMS_ERROR_MESSAGE + \
            f"_CFBcalc; fuel_type: {fuel_type.value}, cbh: {cbh}, fmc: {fmc}"
        raise CFFDRSException(message)
    result = CFFDRS.instance().cffdrs._CFBcalc(FUELTYPE=fuel_type.value, FMC=fmc, SFC=sfc,
                                               ROS=ros, CBH=cbh)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate CFB")


def total_fuel_consumption(
        fuel_type: FuelTypeEnum, cfb: float, sfc: float, pc: float, pdf: float, cfl: float):
    """ Computes Total Fuel Consumption (TFC), which is a required input to calculate Head Fire Intensity.
    TFC is calculated by delegating to cffdrs R package.

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
    """
    if cfb is None or cfl is None:
        message = PARAMS_ERROR_MESSAGE + \
            f"_TFCcalc; fuel_type: {fuel_type.value}, cfb: {cfb}, cfl: {cfl}"
        raise CFFDRSException(message)
    # According to fbp.Rd in cffdrs R package, Crown Fuel Load (CFL) can use default value of 1.0
    # without causing major impacts on final output.
    if pc is None:
        pc = NULL
    if pdf is None:
        pdf = NULL
    result = CFFDRS.instance().cffdrs._TFCcalc(FUELTYPE=fuel_type.value, CFL=cfl, CFB=cfb, SFC=sfc,
                                               PC=pc,
                                               PDF=pdf)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate TFC")


def head_fire_intensity(fuel_type: FuelTypeEnum,
                        percentage_conifer: float,
                        percentage_dead_balsam_fir: float,
                        ros: float,
                        cfb: float,
                        cfl: float,
                        sfc: float):
    """ Computes Head Fire Intensity (HFI) by delegating to cffdrs R package.
    Calculating HFI requires a number of inputs that must be calculated first. This function
    first makes method calls to calculate the necessary intermediary values.
    """

    tfc = total_fuel_consumption(fuel_type, cfb, sfc,
                                 percentage_conifer, percentage_dead_balsam_fir, cfl)
    # Args:
    #   FC:   Fuel Consumption (kg/m^2)
    #   ROS:  Rate of Spread (m/min)
    #
    # Returns:
    #   FI:   Fire Intensity (kW/m)

    result = CFFDRS.instance().cffdrs._FIcalc(FC=tfc, ROS=ros)
    if isinstance(result[0], float):
        return result[0]
    raise CFFDRSException("Failed to calculate FI")


def pandas_to_r_converter(df: pd.DataFrame) -> robjs.vectors.DataFrame:
    """
    Convert pandas dataframe to an R data.frame object

    :param df: Pandas dataframe
    :type df: pd.DataFrame
    :return: R data.frame object
    :rtype: robjs.vectors.DataFrame
    """
    with (robjs.default_converter + pandas2ri.converter).context():
        r_df = robjs.conversion.get_conversion().py2rpy(df)

    return r_df


def hourly_fine_fuel_moisture_code(weatherstream: pd.DataFrame, ffmc_old: float,
                                   time_step: int = 1, calc_step: bool = False, batch: bool = True,
                                   hourly_fwi: bool = False) -> pd.DataFrame:    
    """ Computes hourly FFMC based on noon FFMC using diurnal curve for approximation.
    Delegates the calculation to cffdrs R package.
    https://rdrr.io/rforge/cffdrs/man/hffmc.html

     Args: weatherstream:   Input weather stream data.frame which includes
                            temperature, relative humidity, wind speed,
                            precipitation, hourly value, and bui. More specific
                            info can be found in the hffmc.Rd help file.
                ffmc_old:   ffmc from previous timestep
               time_step:   The time (hours) between previous FFMC and current
                            time.
               calc_step:   Optional for whether time step between two observations is calculated. Default is FALSE, 
                            no calculations. This is used when time intervals are not uniform in the input.
                            (optional)
                   batch:   Single step or iterative (default=TRUE). If multiple weather stations are processed, 
                            an additional "id" column is required in the input weatherstream to label different 
                            stations, and the data needs to be sorted by date/time and "id". 
               hourlyFWI:   calculate hourly ISI, FWI, and DSR. Daily BUI is required.
                            (TRUE/FALSE, default=FALSE)
    
     Returns: A single or multiple hourly ffmc value(s)
    
     From hffmc.Rd:
        weatherstream (required)
            A dataframe containing input variables of hourly weather observations.
            It is important that variable names have to be the same as in the following list, but they
            are case insensitive. The order in which the input variables are entered is not important.

            Typically this dataframe also contains date and hour fields so outputs can be associated 
            with a specific day and time, however these fields are not used in the calculations. If 
            multiple weather stations are being used, a weather station ID field is typically included as well, 
            though this is simply for bookkeeping purposes and does not affect the calculation.
    
        temp (required)  Temperature (centigrade)
        rh   (required)  Relative humidity (%)
        ws   (required)  10-m height wind speed (km/h)
        prec (required)  1-hour rainfall (mm)
        hr   (optional)  Hourly value to calculate sub-hourly ffmc
        bui  (optional)  Daily BUI value for the computation of hourly FWI. It is
                          required when hourlyFWI=TRUE
    """

    # We have to change field names to exactly what the CFFDRS lib expects. 
    # This may need to be adjusted depending on the future data input model, which is currently unknown
    column_name_map = {'temperature':'temp', 'relative_humidity': 'rh', 'wind_speed': 'ws', 'precipitation': 'prec', 'datetime': 'hr'}
    weatherstream = weatherstream.rename(columns=column_name_map)

    r_weatherstream = pandas_to_r_converter(weatherstream)
    try:
        result = CFFDRS.instance().cffdrs.hffmc(r_weatherstream,
                                            ffmc_old=ffmc_old, time_step=time_step, calc_step=calc_step,
                                            batch=batch, hourlyFWI=hourly_fwi)
    
        if isinstance(result, robjs.vectors.FloatVector):
            weatherstream['hffmc'] = list(result)
            return weatherstream
    except rpy2.rinterface_lib.embedded.RRuntimeError as e:
        logger.error(f"An error occurred when calculating hourly ffmc: {e}")
        raise CFFDRSException("Failed to calculate hffmc")
    

def get_ffmc_for_target_hfi(
        fuel_type: FuelTypeEnum,
        percentage_conifer: float,
        percentage_dead_balsam_fir: float,
        bui: float,
        wind_speed: float,
        grass_cure: int,
        crown_base_height: float,
        ffmc: float, fmc: float, cfb: float, cfl: float, target_hfi: float):
    """ Returns a floating point value for minimum FFMC required (holding all other values constant)
        before HFI reaches the target_hfi (in kW/m).
        """
    # start off using the actual FFMC value
    experimental_ffmc = ffmc
    experimental_sfc = surface_fuel_consumption(fuel_type, bui, experimental_ffmc, percentage_conifer)
    experimental_isi = initial_spread_index(experimental_ffmc, wind_speed)
    experimental_ros = rate_of_spread(fuel_type, experimental_isi, bui, fmc, experimental_sfc,
                                      percentage_conifer,
                                      grass_cure, percentage_dead_balsam_fir, crown_base_height)
    experimental_hfi = head_fire_intensity(fuel_type,
                                           percentage_conifer,
                                           percentage_dead_balsam_fir,
                                           experimental_ros, cfb,
                                           cfl, experimental_sfc)
    error_hfi = (target_hfi - experimental_hfi) / target_hfi

   # FFMC has upper bound 101
   # exit condition 1: FFMC of 101 still causes HFI < target_hfi
   # exit condition 2: FFMC of 0 still causes HFI > target_hfi
   # exit condition 3: relative error within 1%

    while abs(error_hfi) > 0.01:
        if experimental_ffmc >= 100.9 and experimental_hfi < target_hfi:
            break
        if experimental_ffmc <= 0.1:
            break
        if error_hfi > 0:  # if the error value is a positive number, make experimental FFMC value bigger
            experimental_ffmc = min(101, experimental_ffmc + ((101 - experimental_ffmc) / 2))
        else:  # if the error value is a negative number, need to make experimental FFMC value smaller
            experimental_ffmc = max(0, experimental_ffmc - ((101 - experimental_ffmc) / 2))
        experimental_isi = initial_spread_index(experimental_ffmc, wind_speed)
        experimental_sfc = surface_fuel_consumption(fuel_type, bui, experimental_ffmc, percentage_conifer)
        experimental_ros = rate_of_spread(fuel_type, experimental_isi, bui, fmc,
                                          experimental_sfc, percentage_conifer,
                                          grass_cure, percentage_dead_balsam_fir, crown_base_height)
        experimental_hfi = head_fire_intensity(fuel_type,
                                               percentage_conifer,
                                               percentage_dead_balsam_fir, experimental_ros,
                                               cfb, cfl, experimental_sfc)
        error_hfi = (target_hfi - experimental_hfi) / target_hfi

    return (experimental_ffmc, experimental_hfi)
