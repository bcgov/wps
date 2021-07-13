""" This module contains functions for computing fire weather metrics.
"""
import logging
from time import time
from typing import Tuple
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
            "_ROScalc ; fuel_type: {fuel_type}, isi: {isi}, bui: {bui}, fmc: {fmc}, sfc: {sfc}".format(
                fuel_type=fuel_type, isi=isi, bui=bui, fmc=fmc, sfc=sfc)
        raise CFFDRSException(message)

    # logger.info('calling _ROScalc(FUELTYPE=%s, ISI=%s, BUI=%s, FMC=%s, SFC=%s, PC=%s, PDF=%s, CC=%s, CBH=%s)',
    #             fuel_type, isi, bui, fmc, sfc, pc, pdf, cc, cbh)

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
#        GFL: Grass Fuel Load (kg/m^2) (0.35 kg/m^2)
# Returns:
#        SFC: Surface Fuel Consumption (kg/m^2)


def surface_fuel_consumption(  # pylint: disable=invalid-name
        fuel_type: str,
        bui: float,
        ffmc: float,
        pc: float):
    """ Computes SFC by delegating to cffdrs R package
        Assumes a standard GFL of 0.35 kg/m ^ 2.
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
        TODO: Find out the minimum fmc date that is passed as D0, for now it's 0. Passing 0 makes FFMCcalc
        calculate it.
     """
    # pylint: disable=protected-access, no-member, line-too-long
    date_of_minimum_foliar_moisture_content = 0
    logger.info('calling _FMCcalc(LAT=%s, LONG=%s, ELV=%s, DJ=%s, D0=%s)', lat,
                long, elv, day_of_year, date_of_minimum_foliar_moisture_content)
    result = CFFDRS.instance().cffdrs._FMCcalc(LAT=lat, LONG=long, ELV=elv,
                                               DJ=day_of_year, D0=date_of_minimum_foliar_moisture_content)
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


def fine_fuel_moisture_code(ffmc: float, temperature: float, relative_humidity: float,
                            precipitation: float, wind_speed: float):
    """ Computes Fine Fuel Moisture Code (FFMC) by delegating to cffdrs R package.
    This is necessary when recalculating certain fire weather indices based on
    user-defined input for wind speed.
    """
    # Args: ffmc_yda:   The Fine Fuel Moisture Code from previous iteration
    #           temp:   Temperature (centigrade)
    #             rh:   Relative Humidity (%)
    #           prec:   Precipitation (mm)
    #             ws:   Wind speed (km/h)
    #
    #
    # Returns: A single ffmc value
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._ffmcCalc(ffmc_yda=ffmc, temp=temperature, rh=relative_humidity,
                                                prec=precipitation, ws=wind_speed)
    return result[0]


def initial_spread_index(ffmc: float, wind_speed: float):
    """ Computes Initial Spread Index (ISI) by delegating to cffdrs R package.
    This is necessary when recalculating ROS/HFI for modified FFMC values. Otherwise,
    should be using the ISI value retrieved from WFWX.
    """
    # Args:
    #   ffmc:   Fine Fuel Moisture Code
    #     ws:   Wind Speed (km/h)
    # fbpMod:   TRUE/FALSE if using the fbp modification at the extreme end
    #
    # Returns:
    #   ISI:    Intial Spread Index
    # pylint: disable=protected-access, no-member
    result = CFFDRS.instance().cffdrs._ISIcalc(ffmc=ffmc, ws=wind_speed)
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


def crown_fraction_burned(fuel_type: str, fmc: float, sfc: float, ros: float, cbh: float) -> float:
    """ Computes Crown Fraction Burned (CFB) by delegating to cffdrs R package.
    Value returned will be between 0-1.
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
        fuel_type: str, cfb: float, sfc: float, pc: float, pdf: float, cfl: float):
    """ Computes Total Fuel Consumption (TFC), which is a required input to calculate Head Fire Intensity.
    TFC is calculated by delegating to cffdrs R package.
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
                        bui: float,
                        ffmc: float,
                        ros: float,
                        cfb: float,
                        cfl: float,
                        sfc: float):
    """ Computes Head Fire Intensity (HFI) by delegating to cffdrs R package.
    Calculating HFI requires a number of inputs that must be calculated first. This function
    first makes method calls to calculate the necessary intermediary values.
    """

    sfc = surface_fuel_consumption(fuel_type, bui, ffmc, percentage_conifer)
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
# \item{weatherstream}{
# A dataframe containing input variables of hourly weather observations.
# It is important that variable names have to be the same as in the following list, but they
# are case insensitive. The order in which the input variables are entered is not important.
# \tabular{lll}{
#     \var{temp} \tab (required) \tab Temperature (centigrade)\cr
#     \var{rh}   \tab (required) \tab Relative humidity (\%)\cr
#     \var{ws}   \tab (required) \tab 10-m height wind speed (km/h)\cr
#     \var{prec} \tab (required) \tab 1-hour rainfall (mm)\cr
#     \var{hr}   \tab (optional) \tab Hourly value to calculate sub-hourly ffmc \cr
#     \var{bui}  \tab (optional) \tab Daily BUI value for the computation of hourly FWI. It is
# required when \code{hourlyFWI=TRUE}.\cr


def get_hourly_ffmc_on_diurnal_curve(ffmc_solar_noon: float, target_hour: float,
                                     temperature: float, relative_humidity: float,
                                     wind_speed: float, precip: float):
    """ Computes hourly FFMC based on noon FFMC using diurnal curve for approximation.
    Delegates the calculation to cffdrs R package.

    ffmc_solar_noon is the forecasted or actual FFMC value for solar noon of the date in question.
    target_hour is the hour of the day (on 24 hour clock) for which hourly FFMC should be calculated
    the weather variables (temperature, rh, wind_speed, precip) is the forecasted or actual weather
    values for solar noon.
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


def get_ffmc_for_target_hfi(fuel_type: str,
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
    experimental_ros = rate_of_spread(fuel_type, experimental_isi, bui, fmc, experimental_sfc, percentage_conifer,
                                      grass_cure, percentage_dead_balsam_fir, crown_base_height)
    experimental_hfi = head_fire_intensity(fuel_type,
                                           percentage_conifer,
                                           percentage_dead_balsam_fir,
                                           bui, experimental_ffmc, experimental_ros, cfb, cfl, experimental_sfc)
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
        experimental_ros = rate_of_spread(fuel_type, experimental_isi, bui, fmc, experimental_sfc, percentage_conifer,
                                          grass_cure, percentage_dead_balsam_fir, crown_base_height)
        experimental_hfi = head_fire_intensity(fuel_type,
                                               percentage_conifer,
                                               percentage_dead_balsam_fir,
                                               bui, experimental_ffmc, experimental_ros, cfb, cfl, experimental_sfc)
        error_hfi = (target_hfi - experimental_hfi) / target_hfi

    return (experimental_ffmc, experimental_hfi)


def get_critical_hours_start(critical_ffmc: float, solar_noon_ffmc: float, temperature: float, relative_humidity: float, wind_speed: float, precip: float):
    """ Returns the hour of day (on 24H clock) at which the hourly FFMC crosses the threshold of critical_ffmc.
    Returns None if the hourly FFMC never reaches critical_ffmc.
    """
    if solar_noon_ffmc >= critical_ffmc:
        logger.info('Solar noon FFMC >= critical FFMC')
        # go back in time in increments of 0.5 hours
        clock_time = 13-0.5  # start from solar noon - 0.5 hours
        while get_hourly_ffmc_on_diurnal_curve(solar_noon_ffmc, clock_time, temperature, relative_humidity, wind_speed, precip) >= critical_ffmc:
            clock_time -= 0.5
            if clock_time == -0.5:
                break
        # add back the half hour that caused FFMC to drop below critical_ffmc (or that pushed time below 0.0)
        clock_time += 0.5
        logger.info('%s', clock_time)
        return clock_time
    else:
        logger.info('Solar noon FFMC %s < critical FFMC %s', solar_noon_ffmc, critical_ffmc)
        # go forward in time in increments of 0.5 hours
        clock_time = 13 + 0.5  # start from solar noon + 0.5 hours
        while get_hourly_ffmc_on_diurnal_curve(solar_noon_ffmc, clock_time, temperature, relative_humidity, wind_speed, precip) < critical_ffmc:
            logger.info('Clock time %s has HFFMC %s', clock_time, get_hourly_ffmc_on_diurnal_curve(
                solar_noon_ffmc, clock_time, temperature, relative_humidity, wind_speed, precip))
            clock_time += 0.5
            if clock_time == 24.0:
                return None
        return clock_time


def get_critical_hours_end(critical_ffmc: float, solar_noon_ffmc: float, critical_hour_start: float, temperature: float, relative_humidity: float, wind_speed: float, precip: float):
    """ Returns the hour of day (on 24H clock) at which the hourly FFMC drops below the threshold of critical_ffmc.
    Should only be called if critical_hour_start is not None.
    If diurnally-adjusted FFMC never drops below critical_ffmc in the day, will return 23.5 (11:30 pm).
    """
    assert critical_hour_start is not None
    clock_time = critical_hour_start + 0.5    # increase time in increments of 0.5 hours
    max_hourly_ffmc = 0.0
    while get_hourly_ffmc_on_diurnal_curve(solar_noon_ffmc, clock_time, temperature, relative_humidity, wind_speed, precip) >= critical_ffmc:
        if get_hourly_ffmc_on_diurnal_curve(solar_noon_ffmc, clock_time, temperature, relative_humidity, wind_speed, precip) > max_hourly_ffmc:
            max_hourly_ffmc = get_hourly_ffmc_on_diurnal_curve(
                solar_noon_ffmc, clock_time, temperature, relative_humidity, wind_speed, precip)
        clock_time += 0.5
        if clock_time == 24.0:
            break
    # subtract the half hour that caused FFMC to drop below critical_ffmc (or that pushed time to 24.0, which
    # corresponds to 12 am of the next day)
    clock_time -= 0.5
    logger.info('max hourly FFMC %s', max_hourly_ffmc)
    return clock_time


def get_critical_hours(target_hfi: int, fuel_type: str, percentage_conifer: float, percentage_dead_balsam_fir: float, bui: float,
                       grass_cure: float, crown_base_height: float,
                       solar_noon_ffmc: float, fmc: float, cfb: float, cfl: float,
                       temperature: float, relative_humidity: float, wind_speed: float,
                       precipitation: float):
    """ Determines the range of critical hours on a 24H clock.
    Critical Hours describes the time range for the given day during which HFI will meet or exceed
    hfi_target value. Critical hours are calculated by determining diurnally-adjusted FFMC values
    that cause HFI >= target_hfi.
    """
    critical_ffmc, resulting_hfi = get_ffmc_for_target_hfi(
        fuel_type, percentage_conifer, percentage_dead_balsam_fir, bui, wind_speed, grass_cure, crown_base_height, solar_noon_ffmc, fmc, cfb, cfl, target_hfi)
    logger.info('Critical FFMC %s, resulting HFI %s; target HFI %s', critical_ffmc, resulting_hfi, target_hfi)
    # Scenario 1: it's not possible for the HFI to reach target_hfi, in which case there will
    # be no critical hours.
    if critical_ffmc >= 100.9 and resulting_hfi < target_hfi:
        logger.info('No critical hours for HFI %s. Critical FFMC %s has HFI %s',
                    target_hfi, critical_ffmc, resulting_hfi)
        return None
    # Scenario 2: the HFI is always >= target_hfi, even when FFMC = 0. In this case, all hours
    # of the day will be critical hours.
    if critical_ffmc == 0.0 and resulting_hfi >= target_hfi:
        logger.info('All hours critical for HFI %s. FFMC %s has HFI %s',
                    target_hfi, critical_ffmc, resulting_hfi)
        return (0.0, 23.5)
    # Scenario 3: there is a critical_ffmc between (0, 101) that corresponds to
    # resulting_hfi >= target_hfi. Now have to determine what hours of the day (if any)
    # will see hourly FFMC (adjusted according to diurnal curve) >= critical_ffmc.
    critical_hour_start = get_critical_hours_start(
        critical_ffmc, solar_noon_ffmc, temperature, relative_humidity, wind_speed, precipitation)
    logger.info('Got critical_hour_start %s', critical_hour_start)
    if critical_hour_start is None:
        return None
    else:
        critical_hour_end = get_critical_hours_end(
            critical_ffmc, solar_noon_ffmc, critical_hour_start, temperature, relative_humidity, wind_speed, precipitation)

    logger.info('Critical hours for target HFI %s are (%s, %s)',
                target_hfi, critical_hour_start, critical_hour_end)
    return (critical_hour_start, critical_hour_end)
