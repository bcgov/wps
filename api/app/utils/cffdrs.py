""" This module contains functions for computing fire weather metrics.
"""
import logging
import math
import rpy2.robjects as robjs
from rpy2.robjects import DataFrame
import rpy2.robjects.conversion as cv
from rpy2.rinterface import NULL
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


# Computable: SFC, FMC
# To store in DB: PC, PDF, CC, CBH (attached to fuel type, red book)
PARAMS_ERROR_MESSAGE = "One or more params passed to R call is None."


def correct_wind_azimuth(wind_direction: float):
    """
    #Corrections to reorient Wind Azimuth(WAZ)
    WAZ <- WD + pi
    WAZ <- ifelse(WAZ > 2 * pi, WAZ - 2 * pi, WAZ)
    """
    waz = wind_direction + math.pi
    if waz > 2 * math.pi:
        return waz - 2 * math.pi
    return waz


def calculate_net_effective_windspeed(fuel_type: str,  # pylint: disable=too-many-arguments, disable=invalid-name
                                      ffmc: float,
                                      bui: float,
                                      ws: float,
                                      waz: float,
                                      gs: float,
                                      saz: float,
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
    # pylint: disable=protected-access, no-member
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
        result = CFFDRS.instance().cffdrs._Slopecalc(FUELTYPE=fuel_type,
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
        return result[0]
    return ws


def flank_rate_of_spread(ros: float, bros: float, lb: float):  # pylint: disable=invalid-name
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
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._FROScalc(ROS=ros, BROS=bros, LB=lb)
    return result[0]


def back_rate_of_spread(fuel_type: str,  # pylint: disable=too-many-arguments, disable=invalid-name
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
            "_BROScalc ; fuel_type: {fuel_type}, ffmc: {ffmc}, bui: {bui}, fmc: {fmc}, sfc: {sfc}".format(
                fuel_type=fuel_type, ffmc=ffmc, bui=bui, fmc=fmc, sfc=sfc)
        raise CFFDRSException(message)

    if pc is None:
        pc = NULL
    if cc is None:
        cc = NULL
    if pdf is None:
        pdf = NULL
    if cbh is None:
        cbh = NULL
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._BROScalc(FUELTYPE=fuel_type,
                                                FFMC=ffmc,
                                                BUI=bui,
                                                WSV=wsv,
                                                FMC=fmc,
                                                SFC=sfc,
                                                PC=pc,
                                                PDF=pdf,
                                                CC=cc,
                                                CBH=cbh)
    return result[0]


def bui_calc(dmc: float, dc: float):  # pylint: disable=invalid-name
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
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._buiCalc(dmc=dmc, dc=dc)
    return result[0]


def rate_of_spread_t(fuel_type: str,
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
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._ROStcalc(FUELTYPE=fuel_type,
                                                ROSeq=ros_eq,
                                                HR=minutes_since_ignition,
                                                CFB=cfb)
    return result[0]


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
            "_ROScalc ; fuel_type: {fuel_type}, isi: {isi}, bui: {bui}, fmc: {fmc}, sfc: {sfc}".format(
                fuel_type=fuel_type, isi=isi, bui=bui, fmc=fmc, sfc=sfc)
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
    # pylint: disable=protected-access, no-member
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


def surface_fuel_consumption(  # pylint: disable=invalid-name
        fuel_type: str,
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
            "_SFCcalc; fuel_type: {fuel_type}, bui: {bui}, ffmc: {ffmc}".format(
                fuel_type=fuel_type, bui=bui, ffmc=ffmc)
        raise CFFDRSException(message)
    if pc is None:
        pc = NULL
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._SFCcalc(FUELTYPE=fuel_type,
                                               BUI=bui,
                                               FFMC=ffmc,
                                               PC=pc,
                                               GFL=0.35)
    return result[0]


def fire_distance(fuel_type: str, ros_eq: float, hr: int, cfb: float):  # pylint: disable=invalid-name
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
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._DISTtcalc(fuel_type, ros_eq, hr, cfb)
    return result[0]


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
    # pylint: disable=protected-access, no-member
    logger.debug('calling _FMCcalc(LAT=%s, LONG=%s, ELV=%s, DJ=%s, D0=%s)', lat,
                 long, elv, day_of_year, date_of_minimum_foliar_moisture_content)
    if long < 0:
        long = -long
    result = CFFDRS.instance().cffdrs._FMCcalc(LAT=lat, LONG=long, ELV=elv,
                                               DJ=day_of_year, D0=date_of_minimum_foliar_moisture_content)
    return result[0]


def length_to_breadth_ratio(fuel_type: str, wind_speed: float):
    """ Computes L/B ratio by delegating to cffdrs R package

    # Args:
    #   FUELTYPE: The Fire Behaviour Prediction FuelType
    #        WSV: The Wind Speed (km/h)
    # Returns:
    #   LB: Length to Breadth ratio
    """
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._LBcalc(FUELTYPE=fuel_type, WSV=wind_speed)
    return result[0]


def length_to_breadth_ratio_t(fuel_type: str,  # pylint: disable=invalid-name
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
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._LBtcalc(FUELTYPE=fuel_type, LB=lb,
                                               HR=time_since_ignition, CFB=cfb)
    return result[0]


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

    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._ffmcCalc(ffmc_yda=ffmc, temp=temperature, rh=relative_humidity,
                                                prec=precipitation, ws=wind_speed)
    return result[0]


def initial_spread_index(ffmc: float, wind_speed: float, fbpMod: bool = False):  # pylint: disable=invalid-name
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
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._ISIcalc(ffmc=ffmc, ws=wind_speed, fbpMod=fbpMod)
    return result[0]


def crown_fraction_burned(fuel_type: str, fmc: float, sfc: float, ros: float, cbh: float) -> float:
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
    # pylint: disable=protected-access, no-member
    if cbh is None:
        cbh = NULL
    if cbh is None or fmc is None:
        message = PARAMS_ERROR_MESSAGE + \
            "_CFBcalc; fuel_type: {fuel_type}, cbh: {cbh}, fmc: {fmc}".format(
                fuel_type=fuel_type, cbh=cbh, fmc=fmc)
        raise CFFDRSException(message)
    result = CFFDRS.instance().cffdrs._CFBcalc(FUELTYPE=fuel_type, FMC=fmc, SFC=sfc,
                                               ROS=ros, CBH=cbh)
    return result[0]


def total_fuel_consumption(  # pylint: disable=invalid-name
        fuel_type: str, cfb: float, sfc: float, pc: float, pdf: float, cfl: float):
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
            "_TFCcalc; fuel_type: {fuel_type}, cfb: {cfb}, cfl: {cfl}".format(
                fuel_type=fuel_type, cfb=cfb, cfl=cfl)
        raise CFFDRSException(message)
    # According to fbp.Rd in cffdrs R package, Crown Fuel Load (CFL) can use default value of 1.0
    # without causing major impacts on final output.
    if pc is None:
        pc = NULL
    if pdf is None:
        pdf = NULL
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._TFCcalc(FUELTYPE=fuel_type, CFL=cfl, CFB=cfb, SFC=sfc,
                                               PC=pc,
                                               PDF=pdf)
    return result[0]


def head_fire_intensity(fuel_type: str,
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

    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._FIcalc(FC=tfc, ROS=ros)
    return result[0]


def get_hourly_ffmc_on_diurnal_curve(ffmc_solar_noon: float, target_hour: float,
                                     temperature: float, relative_humidity: float,
                                     wind_speed: float, precip: float):
    """ Computes hourly FFMC based on noon FFMC using diurnal curve for approximation.
    Delegates the calculation to cffdrs R package.

    ffmc_solar_noon is the forecasted or actual FFMC value for solar noon of the date in question.
    target_hour is the hour of the day (on 24 hour clock) for which hourly FFMC should be calculated
    the weather variables (temperature, rh, wind_speed, precip) is the forecasted or actual weather
    values for solar noon.

    # Args: weatherstream:   Input weather stream data.frame which includes
    #                        temperature, relative humidity, wind speed,
    #                        precipitation, hourly value, and bui. More specific
    #                        info can be found in the hffmc.Rd help file.
    #            ffmc_old:   ffmc from previous timestep
    #           time.step:   The time (hours) between previous FFMC and current
    #                        time.
    #           calc.step:   Whether time step between 2 obs is calculated
    #                        (optional)
    #               batch:   Single step or iterative (default=TRUE)
    #           hourlyFWI:   Can calculated hourly ISI & FWI as well
    #                        (TRUE/FALSE, default=FALSE)
    #
    # Returns: A single or multiple hourly ffmc value(s)
    #
    # From hffmc.Rd:
    # {weatherstream}{
    # A dataframe containing input variables of hourly weather observations.
    # It is important that variable names have to be the same as in the following list, but they
    # are case insensitive. The order in which the input variables are entered is not important.
    #
    #     temp (required)  Temperature (centigrade)
    #     rh   (required)  Relative humidity (%)
    #     ws   (required)  10-m height wind speed (km/h)
    #     prec (required)  1-hour rainfall (mm)
    #     hr   (optional)  Hourly value to calculate sub-hourly ffmc
    #     bui  (optional)  Daily BUI value for the computation of hourly FWI. It is
    # required when hourlyFWI=TRUE
    """
    time_offset = target_hour - 13  # solar noon
    # build weather_data dictionary to be passed as weatherstream
    weather_data = {
        'hr': 13.0,
        'temp': temperature,
        'rh': relative_humidity,
        'ws': wind_speed,
        'prec': precip / 24     # the precip received will be based on the previous 24 hours, but the
        # R function requires 1-hour rainfall. We don't have hourly data, so the best we can do is
        # take the mean amount of precip for the past 24 hours. This is a liberal approximation
        # with a lot of hand-waving.
    }
    weather_data = DataFrame(weather_data)
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs.hffmc(weatherstream=weather_data,
                                            ffmc_old=ffmc_solar_noon, time_step=time_offset)
    return result[0]


def get_ffmc_for_target_hfi(    # pylint: disable=too-many-arguments
        fuel_type: str,
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
            experimental_ffmc = min(101, experimental_ffmc + ((101 - experimental_ffmc)/2))
        else:  # if the error value is a negative number, need to make experimental FFMC value smaller
            experimental_ffmc = max(0, experimental_ffmc - ((101 - experimental_ffmc)/2))
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
