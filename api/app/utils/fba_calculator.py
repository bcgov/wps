""" Fire Behaviour Analysis Calculator Tool
"""
import math
import os
from datetime import date
from typing import List, Optional
import logging
import pandas as pd
from app.schemas.observations import WeatherReading
from app.utils.singleton import Singleton
from app.utils.hfi_calculator import FUEL_TYPE_LOOKUP
from app.utils import cffdrs
from app.utils.time import convert_utc_to_pdt, get_hour_20_from_date, get_julian_date

logger = logging.getLogger(__name__)


class CannotCalculateFireTypeError(Exception):
    """ Exception thrown when fire type cannot be established """


@Singleton
class DiurnalFFMCLookupTable():
    """ Singleton that loads diurnal FFMC lookup tables from Red Book once, for reuse.
    afternoon_overnight.csv is Table 4.1 from Red Book, 3rd ed., 2018;
    morning.csv is Table 4.2 from Red Book, 3rd ed., 2018.
    """

    def __init__(self):
        filename = os.path.join(os.path.dirname(__file__),
                                '../data/diurnal_ffmc_lookups/afternoon_overnight.csv')
        with open(filename, 'rb') as afternoon_file:
            afternoon_df = pd.read_csv(afternoon_file)
        # Pylint thinks that afternoon_df's type is TextFileReader. It isn't - it's a pandas dataframe.
        # pylint: disable=no-member
        afternoon_df.columns = afternoon_df.columns.astype(int)
        afternoon_df.set_index(17, inplace=True)

        filename = os.path.join(os.path.dirname(__file__),
                                '../data/diurnal_ffmc_lookups/afternoon_overnight.csv')
        with open(filename, 'rb') as morning_file:
            morning_df = pd.read_csv(morning_file, header=[0, 1])
        prev_days_daily_ffmc_keys = morning_df.iloc[:, 0].values
        df_col_labels = morning_df.columns.values
        hour_lookup_keys = ['']
        rh_lookup_keys = ['']
        # Pylint says that df_col_labels is not an iterable. Pylint wrong.
        # pylint: disable=not-an-iterable
        for level_1, level_2 in df_col_labels:
            if 'Unnamed' in str(level_2):
                continue
            if 'Unnamed' not in str(level_1):
                hour = int(level_1)
                hour_lookup_keys += 3 * [hour]
            rh_lookup_keys += [level_2]

        # Pylint thinks that morning_df's type is TextFileReader. It isn't - it's a pandas dataframe.
        # pylint: disable=no-member
        morning_df.set_index(prev_days_daily_ffmc_keys, inplace=True)
        header = pd.MultiIndex.from_tuples(list(zip(hour_lookup_keys, rh_lookup_keys)), names=['hour', 'RH'])
        morning_df.columns = header
        morning_df.drop(columns=[('', '')], inplace=True)

        self.afternoon_df = afternoon_df
        self.morning_df = morning_df


class FBACalculatorWeatherStation():  # pylint: disable=too-many-instance-attributes
    """ Inputs for Fire Behaviour Advisory Calculator """

    def __init__(self,  # pylint: disable=too-many-arguments, too-many-locals
                 elevation: int, fuel_type: str,
                 time_of_interest: date, percentage_conifer: float,
                 percentage_dead_balsam_fir: float, grass_cure: float,
                 crown_base_height: int, lat: float, long: float, bui: float, ffmc: float, isi: float,
                 wind_speed: float, wind_direction: float, temperature: float, relative_humidity: float,
                 precipitation: float, status: str, prev_day_daily_ffmc: float,
                 last_observed_morning_rh_values: dict):
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
        self.wind_direction = wind_direction
        self.temperature = temperature
        self.relative_humidity = relative_humidity
        self.precipitation = precipitation
        self.status = status
        self.prev_day_daily_ffmc = prev_day_daily_ffmc
        self.last_observed_morning_rh_values = last_observed_morning_rh_values

    def __str__(self) -> str:
        return 'lat {}, long {}, elevation {}, fuel_type {}, time_of_interest {}, percentage_conifer {},\
            percentage_dead_balsam_fir {}, grass_cure {}, crown_base_height {}, bui {}, ffmc {}, isi {},\
            prev_day_daily_ffmc {}, wind_speed {}, temperature {}, relative_humidity {}, precipitation {}, status {}'\
                .format(self.lat, self.long,
                        self.elevation, self.fuel_type, self.time_of_interest, self.percentage_conifer,
                        self.percentage_dead_balsam_fir, self.grass_cure, self.crown_base_height,
                        self.bui, self.ffmc, self.isi, self.prev_day_daily_ffmc, self.wind_speed,
                        self.temperature, self.relative_humidity, self.precipitation, self.status)


class FireBehaviourAdvisory():  # pylint: disable=too-many-instance-attributes
    """ Class containing the results of the fire behaviour advisory calculation. """

    def __init__(self,  # pylint: disable=too-many-arguments
                 hfi: float, ros: float, fire_type: str, cfb: float, flame_length: float,
                 sixty_minute_fire_size: float, thirty_minute_fire_size: float,
                 critical_hours_hfi_4000: Optional[str],
                 critical_hours_hfi_10000: Optional[str]):
        self.hfi = hfi
        self.ros = ros
        self.fire_type = fire_type  # TODO: make this an enum
        self.cfb = cfb
        self.flame_length = flame_length
        self.sixty_minute_fire_size = sixty_minute_fire_size
        self.thirty_minute_fire_size = thirty_minute_fire_size
        self.critical_hours_hfi_4000 = critical_hours_hfi_4000
        self.critical_hours_hfi_10000 = critical_hours_hfi_10000


def calculate_fire_behaviour_advisory(station: FBACalculatorWeatherStation) -> FireBehaviourAdvisory:
    """ Transform from the raw daily json object returned by wf1, to our fba_calc.StationResponse object.
    """
    # pylint: disable=too-many-locals
    # time of interest will be the same for all stations.
    time_of_interest = get_hour_20_from_date(station.time_of_interest)

    if station.fuel_type == 'C1':
        # The day 144 is the average date for the minimum foliar moisture content in the boreal regions of
        # Canada. It is usually pretty close maybe 7 days in either direction.
        date_of_minimum_foliar_moisture_content = 144
    else:
        # Setting to 0 will cause CFFDRS to figure it out by itself.
        date_of_minimum_foliar_moisture_content = 0

    fmc = cffdrs.foliar_moisture_content(
        station.lat, station.long, station.elevation,
        get_julian_date(time_of_interest),
        date_of_minimum_foliar_moisture_content=date_of_minimum_foliar_moisture_content)
    sfc = cffdrs.surface_fuel_consumption(station.fuel_type, station.bui,
                                          station.ffmc, station.percentage_conifer)
    lb_ratio = cffdrs.length_to_breadth_ratio(station.fuel_type, station.wind_speed)
    ros = cffdrs.rate_of_spread(station.fuel_type, isi=station.isi, bui=station.bui, fmc=fmc, sfc=sfc,
                                pc=station.percentage_conifer,
                                cc=station.grass_cure,
                                pdf=station.percentage_dead_balsam_fir,
                                cbh=station.crown_base_height)
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
                                     ros=ros, cfb=cfb, cfl=cfl, sfc=sfc)
    critical_hours_4000 = get_critical_hours(4000, station.fuel_type, station.percentage_conifer,
                                             station.percentage_dead_balsam_fir, station.bui,
                                             station.grass_cure,
                                             station.crown_base_height, station.ffmc, fmc, cfb, cfl,
                                             station.wind_speed, station.prev_day_daily_ffmc,
                                             station.last_observed_morning_rh_values)
    critical_hours_10000 = get_critical_hours(10000, station.fuel_type, station.percentage_conifer,
                                              station.percentage_dead_balsam_fir, station.bui,
                                              station.grass_cure,
                                              station.crown_base_height, station.ffmc, fmc, cfb, cfl,
                                              station.wind_speed, station.prev_day_daily_ffmc,
                                              station.last_observed_morning_rh_values)

    fire_type = get_fire_type(fuel_type=station.fuel_type, crown_fraction_burned=cfb)
    flame_length = get_approx_flame_length(hfi)

    wind_azimuth = cffdrs.correct_wind_azimuth(station.wind_direction)
    slope_azimuth = None  # a.k.a. SAZ
    ground_slope = 0  # right now we're not taking slope into account
    wsv = cffdrs.calculate_net_effective_windspeed(fuel_type=station.fuel_type, ffmc=station.ffmc,
                                                   bui=station.bui, ws=station.wind_speed, waz=wind_azimuth,
                                                   gs=ground_slope,
                                                   saz=slope_azimuth, fmc=fmc, sfc=sfc,
                                                   pc=station.percentage_conifer,
                                                   cc=station.grass_cure,
                                                   pdf=station.percentage_dead_balsam_fir,
                                                   cbh=station.crown_base_height,
                                                   isi=station.isi)

    bros = cffdrs.back_rate_of_spread(fuel_type=station.fuel_type, ffmc=station.ffmc, bui=station.bui,
                                      wsv=wsv,
                                      fmc=fmc, sfc=sfc,
                                      pc=station.percentage_conifer,
                                      cc=station.grass_cure,
                                      pdf=station.percentage_dead_balsam_fir,
                                      cbh=station.crown_base_height)

    sixty_minute_fire_size = get_fire_size(station.fuel_type, ros, bros, 60, cfb, lb_ratio)
    thirty_minute_fire_size = get_fire_size(station.fuel_type, ros, bros, 30, cfb, lb_ratio)

    return FireBehaviourAdvisory(
        hfi=hfi, ros=ros, fire_type=fire_type, cfb=cfb, flame_length=flame_length,
        sixty_minute_fire_size=sixty_minute_fire_size,
        thirty_minute_fire_size=thirty_minute_fire_size,
        critical_hours_hfi_4000=critical_hours_4000,
        critical_hours_hfi_10000=critical_hours_10000)


def get_30_minutes_fire_size(length_breadth_ratio: float, rate_of_spread: float):
    """ Returns estimated fire size in hectares after 30 minutes, based on LB ratio and ROS.
    Formula derived from sample HFI workbook (see HFI_spreadsheet.md).

    30 min fire size = (pi * spread^2) / (40,000 * LB ratio)
    where spread = 30 * ROS
    """
    # TODO: this function deprecated, please delete.
    return (math.pi * math.pow(30 * rate_of_spread, 2)) / (40000 * length_breadth_ratio)


def get_60_minutes_fire_size(length_breadth_ratio: float, rate_of_spread: float):
    """ Returns estimated fire size in hectares after 60 minutes, based on LB ratio and ROS.
    Formula derived from sample HFI workbook (see HFI_spreadsheet.md)

    60 min fire size = (pi * spread^2) / (40,000 * LB ratio)
    where spread = 60 * ROS

    Excel spreadsheet:
    ((3.14*(SPREAD/2)*((SPREAD/2)/LB))/10000)
    in python:
    spread = rate_of_spread * 60
    return (math.pi*(spread/2)*((spread/2)/length_breadth_ratio))/10000
    """
    # TODO: this function deprecated, please delete.
    return (math.pi * math.pow(60.0 * rate_of_spread, 2)) / (40000.0 * length_breadth_ratio)


def get_fire_size(fuel_type: str, ros: float, bros: float, ellapsed_minutes: int, cfb: float,
                  lb_ratio: float):
    """
    Fire size based on Eq. 8 (Alexander, M.E. 1985. Estimating the length-to-breadth ratio of elliptical
    forest fire patterns.).
    """
    # Using acceleration:
    fire_spread_distance = cffdrs.fire_distance(fuel_type, ros+bros, ellapsed_minutes, cfb)
    length_to_breadth_at_time = cffdrs.length_to_breadth_ratio_t(fuel_type, lb_ratio, ellapsed_minutes, cfb)
    # Not using acceleration:
    # fros = cffdrs.flank_rate_of_spread(ros, bros, lb_ratio)
    # # Flank Fire Spread Distance a.k.a. DF in R/FBPcalc.r
    # flank_fire_spread_distance = (ros + bros) / (2.0 * fros)
    # length_to_breadth_at_time = flank_fire_spread_distance
    # fire_spread_distance = (ros + bros) * ellapsed_minutes

    # Essentially using Eq. 8 (Alexander, M.E. 1985. Estimating the length-to-breadth ratio of elliptical
    # forest fire patterns.) - but feeding it L/B and ROS from CFFDRS.
    return math.pi / (4.0 * length_to_breadth_at_time) * math.pow(fire_spread_distance, 2.0) / 10000.0


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


def get_afternoon_overnight_diurnal_ffmc(hour_of_interest: int, daily_ffmc: float):
    """ Returns the diurnal FFMC (an approximation) estimated for the given hour_of_interest,
    based on the daily_ffmc.
    Hour_of_interest should be expressed in PDT time zone, and can only be between the hours
    1300 and 0700 the next morning. Otherwise, must use different function.
    """

    # pylint: disable=protected-access, no-member
    afternoon_df = DiurnalFFMCLookupTable.instance().afternoon_df

    # find index (solar noon FFMC) of afternoon_df that is nearest to solar_noon_ffmc value
    row = afternoon_df.iloc[abs((afternoon_df.index - daily_ffmc)).argsort()[:1]]
    if hour_of_interest >= 23.5:
        hour_of_interest = hour_of_interest - 24.0
    # determine minimum absolute value difference between hour_of_interest and column labels
    min_abs_diff = abs(row.columns - hour_of_interest).sort_values()[0]
    row_index = row.columns.get_loc(min_abs_diff + hour_of_interest)
    return row.iloc[:, row_index].values[0]


def get_morning_diurnal_ffmc(hour_of_interest: int, prev_day_daily_ffmc: float, hourly_rh: float):
    """ Returns the diurnal FFMC (an approximation) estimated for the given hour_of_interest,
    based on the estimated RH value for the hour_of_interest.
    """
    # pylint: disable=protected-access, no-member
    morning_df = DiurnalFFMCLookupTable.instance().morning_df

    # find index (previous day's daily FFMC) of morning_df that is nearest to prev_day_daily_ffmc
    row = morning_df.iloc[abs((morning_df.index - prev_day_daily_ffmc)).argsort()[:1]]

    # the RH column labels are strings expressing ranges. Must extract lower and upper bounds
    for range_rh_value in row[hour_of_interest].columns:
        bounds = str(range_rh_value).split('-')
        lower_bound = int(bounds[0])
        upper_bound = int(bounds[1])
        if lower_bound <= hourly_rh <= upper_bound:
            return row[hour_of_interest][range_rh_value].values[0]

    # we should never actually reach this return statement
    return None


def get_critical_hours_start(critical_ffmc: float, daily_ffmc: float,
                             prev_day_daily_ffmc: float, last_observed_morning_rh_values: dict):
    """ Returns the hour of day (on 24H clock) at which the hourly FFMC crosses the
    threshold of critical_ffmc.
    Returns None if the hourly FFMC never reaches critical_ffmc.
    """
    if daily_ffmc < critical_ffmc:
        logger.info('Daily FFMC %s < critical FFMC %s', daily_ffmc, critical_ffmc)
        # Daily FFMC represents peak burning, so diurnal hourly FFMC will never be higher than daily FFMC
        # if daily FFMC < critical FFMC, station will never reach critical FFMC at any hour of the day
        return None
    # else daily_ffmc >= critical_ffmc
    logger.info('Daily FFMC %s >= critical FFMC %s', daily_ffmc, critical_ffmc)
    solar_noon_diurnal_ffmc = get_afternoon_overnight_diurnal_ffmc(13, daily_ffmc)
    if solar_noon_diurnal_ffmc >= critical_ffmc:
        clock_time = 12.0
        hourly_rh = last_observed_morning_rh_values[clock_time]
        while get_morning_diurnal_ffmc(clock_time, prev_day_daily_ffmc, hourly_rh) >= critical_ffmc:
            clock_time -= 1.0
            if clock_time < 7.0:
                break
            hourly_rh = last_observed_morning_rh_values[clock_time]
        # add back the hour that caused FFMC to drop below critical_ffmc
        clock_time += 1.0
        return clock_time
    # else the start of critical hours is sometime in the afternoon (between 12:00 and 17:00)
    clock_time = 16.0
    while get_afternoon_overnight_diurnal_ffmc(clock_time, daily_ffmc) >= critical_ffmc:
        logger.info('At %s, hourly diurnal FFMC is %s', clock_time,
                    get_afternoon_overnight_diurnal_ffmc(clock_time, daily_ffmc))
        clock_time -= 1.0
    # add back the hour that caused FFMC to drop below critical_ffmc
    clock_time += 1.0
    return clock_time


def get_critical_hours_end(critical_ffmc: float, solar_noon_ffmc: float, critical_hour_start: float):
    """ Returns the hour of day (on 24H clock) at which the hourly FFMC drops below
    the threshold of critical_ffmc.
    Should only be called if critical_hour_start is not None.
    """
    if critical_hour_start is None:
        return None
    if critical_hour_start < 13:
        # if critical_hour_start is in the morning, we know that based on the diurnal curve,
        # the critical hour is going to extend into the afternoon, so set clock_time to then
        clock_time = 14.0
    else:
        clock_time = critical_hour_start + 1.0    # increase time in increments of 1 hours

    while get_afternoon_overnight_diurnal_ffmc(clock_time, solar_noon_ffmc) >= critical_ffmc:
        clock_time += 1.0
        if clock_time >= 32:  # break if clock_time is now 08:00 of the next day
            break
    # subtract the hour that caused FFMC to drop below critical_ffmc
    clock_time -= 1.0
    if clock_time >= 24.0:
        clock_time = clock_time - 24.0
    return clock_time


def get_critical_hours(  # pylint: disable=too-many-arguments
        target_hfi: int, fuel_type: str, percentage_conifer: float,
        percentage_dead_balsam_fir: float, bui: float,
        grass_cure: float, crown_base_height: float,
        daily_ffmc: float, fmc: float, cfb: float, cfl: float,
        wind_speed: float, prev_daily_ffmc: float,
        last_observed_morning_rh_values: dict):
    """ Determines the range of critical hours on a 24H clock.
    Critical Hours describes the time range for the given day during which HFI will meet or exceed
    hfi_target value. Critical hours are calculated by determining diurnally-adjusted FFMC values
    that cause HFI >= target_hfi.
    """
    critical_ffmc, resulting_hfi = cffdrs.get_ffmc_for_target_hfi(
        fuel_type, percentage_conifer, percentage_dead_balsam_fir, bui, wind_speed,
        grass_cure, crown_base_height, daily_ffmc, fmc, cfb, cfl, target_hfi)
    logger.info('Critical FFMC %s, resulting HFI %s; target HFI %s', critical_ffmc,
                resulting_hfi, target_hfi)
    # Scenario 1 (resulting_hfi < target_hfi) - will happen when it's impossible to get
    # a HFI value large enough to >= target_hfi, because FFMC influences the HFI value,
    # and FFMC has an upper bound of 101. So basically, in this scenario the resulting_hfi
    # would equal the resulting HFI when FFMC is set to 101.
    if critical_ffmc >= 100.9 and resulting_hfi < target_hfi:
        logger.info('No critical hours for HFI %s. Critical FFMC %s has HFI %s',
                    target_hfi, critical_ffmc, resulting_hfi)
        return None
    # Scenario 2: the HFI is always >= target_hfi, even when FFMC = 0. In this case, all hours
    # of the day will be critical hours.
    if critical_ffmc == 0.0 and resulting_hfi >= target_hfi:
        logger.info('All hours critical for HFI %s. FFMC %s has HFI %s',
                    target_hfi, critical_ffmc, resulting_hfi)
        return '13:00 - 7:00'
    # Scenario 3: there is a critical_ffmc between (0, 101) that corresponds to
    # resulting_hfi >= target_hfi. Now have to determine what hours of the day (if any)
    # will see hourly FFMC (adjusted according to diurnal curve) >= critical_ffmc.
    critical_hours_start = get_critical_hours_start(
        critical_ffmc, daily_ffmc, prev_daily_ffmc, last_observed_morning_rh_values)
    if critical_hours_start is None:
        return None
    critical_hours_end = get_critical_hours_end(
        critical_ffmc, daily_ffmc, critical_hours_start)

    # format result as string
    critical_hours_start = str(critical_hours_start).replace('.', ':')
    critical_hours_end = str(critical_hours_end).replace('.', ':')
    critical_hours_start = critical_hours_start.replace(':0', ':00').replace(':5', ':30')
    critical_hours_end = critical_hours_end.replace(':0', ':00').replace(':5', ':30')
    response_string = critical_hours_start + ' - ' + critical_hours_end
    return response_string


def build_hourly_rh_dict(hourly_observations: List[WeatherReading]):
    """ Builds a dictionary of the most recently observed RH values between 0700 and 1200 H
    for a station. Returns the dictionary.
    """
    hourly_observations.sort(key=lambda x: x.datetime, reverse=True)
    relevant_hours = [7.0, 8.0, 9.0, 10.0, 11.0, 12.0]
    rh_dict = {
        7.0: None,
        8.0: None,
        9.0: None,
        10.0: None,
        11.0: None,
        12.0: None
    }
    for obs in hourly_observations:
        obs.datetime = convert_utc_to_pdt(obs.datetime)
        if len(relevant_hours) == 0:
            break
        if obs.datetime.hour in relevant_hours and rh_dict[obs.datetime.hour] is None:
            rh_dict[obs.datetime.hour] = obs.relative_humidity
            relevant_hours.remove(obs.datetime.hour)

    return rh_dict
