""" Fire Behaviour Analysis Calculator Tool
"""
from enum import Enum
import math
import os
from typing import List
import logging
import pandas as pd
from app.fire_behaviour.fuel_types import is_grass_fuel_type
from app.schemas.fba_calc import FuelTypeEnum
from app.schemas.observations import WeatherReading
from app.schemas.fba_calc import CriticalHoursHFI
from app.utils.singleton import Singleton
from app.fire_behaviour import cffdrs, c7b
from app.utils.time import convert_utc_to_pdt, get_julian_date_now

logger = logging.getLogger(__name__)


class FireTypeEnum(str, Enum):
    """ Enumerator for the three different fire types. """
    SURFACE = 'SUR'
    INTERMITTENT_CROWN = 'IC'
    CONTINUOUS_CROWN = 'CC'


class CannotCalculateFireTypeError(Exception):
    """ Exception thrown when fire type cannot be established """


class FireBehaviourPredictionInputError(Exception):
    """ Exception thrown when there is something wrong with the input required to calculate a fire behaviour
    prediction. """


@Singleton
class DiurnalFFMCLookupTable():
    """ Singleton that loads diurnal FFMC lookup tables from Red Book once, for reuse.
    afternoon_overnight.csv is Table 4.1 from Red Book, 3rd ed., 2018;
    morning.csv is Table 4.2 from Red Book, 3rd ed., 2018.
    """

    def __init__(self):
        afternoon_filename = os.path.join(os.path.dirname(__file__),
                                          '../data/diurnal_ffmc_lookups/afternoon_overnight.csv')
        with open(afternoon_filename, 'rb') as afternoon_file:
            afternoon_df = pd.read_csv(afternoon_file)
        afternoon_df.columns = afternoon_df.columns.astype(int)
        afternoon_df.set_index(17, inplace=True)

        morning_filename = os.path.join(os.path.dirname(__file__),
                                        '../data/diurnal_ffmc_lookups/morning.csv')
        with open(morning_filename, 'rb') as morning_file:
            morning_df = pd.read_csv(morning_file, header=[0, 1])
        prev_days_daily_ffmc_keys = morning_df.iloc[:, 0].values
        df_col_labels = morning_df.columns.values
        hour_lookup_keys = ['']
        rh_lookup_keys = ['']

        for level_1, level_2 in df_col_labels:
            if 'Unnamed' in str(level_2):
                continue
            if 'Unnamed' not in str(level_1):
                hour = int(level_1)
                hour_lookup_keys += 3 * [hour]
            rh_lookup_keys += [level_2]

        morning_df.set_index(prev_days_daily_ffmc_keys, inplace=True)
        header = pd.MultiIndex.from_tuples(list(zip(hour_lookup_keys, rh_lookup_keys)), names=['hour', 'RH'])
        morning_df.columns = header
        morning_df.drop(columns=[('', '')], inplace=True)

        self.afternoon_df = afternoon_df
        self.morning_df = morning_df


def calculate_cfb(fuel_type: FuelTypeEnum, fmc: float, sfc: float, ros: float, cbh: float):
    """ Calculate the crown fraction burned  (returning 0 for fuel types without crowns to burn) """
    if fuel_type in [FuelTypeEnum.D1, FuelTypeEnum.O1A, FuelTypeEnum.O1B,
                     FuelTypeEnum.S1, FuelTypeEnum.S2, FuelTypeEnum.S3]:
        # These fuel types don't have a crown fraction burnt. But CFB is needed for other calculations,
        # so we go with 0.
        cfb = 0
    elif cbh is None:
        # We can't calculate cfb without a crown base height!
        cfb = None
    else:
        cfb = cffdrs.crown_fraction_burned(fuel_type, fmc=fmc, sfc=sfc, ros=ros, cbh=cbh)
    return cfb


def get_fire_size(fuel_type: FuelTypeEnum, ros: float, bros: float, elapsed_minutes: int, cfb: float,
                  lb_ratio: float):
    """
    Fire size based on Eq. 8 (Alexander, M.E. 1985. Estimating the length-to-breadth ratio of elliptical
    forest fire patterns.).
    """
    if fuel_type is None or ros is None or bros is None or lb_ratio is None:
        raise cffdrs.CFFDRSException()
    # Using acceleration:
    fire_spread_distance = cffdrs.fire_distance(fuel_type, ros + bros, elapsed_minutes, cfb)
    length_to_breadth_at_time = cffdrs.length_to_breadth_ratio_t(fuel_type, lb_ratio, elapsed_minutes, cfb)
    # Not using acceleration:
    # fros = cffdrs.flank_rate_of_spread(ros, bros, lb_ratio)
    # # Flank Fire Spread Distance a.k.a. DF in R/FBPcalc.r
    # flank_fire_spread_distance = (ros + bros) / (2.0 * fros)
    # length_to_breadth_at_time = flank_fire_spread_distance
    # fire_spread_distance = (ros + bros) * elapsed_minutes

    # Essentially using Eq. 8 (Alexander, M.E. 1985. Estimating the length-to-breadth ratio of elliptical
    # forest fire patterns.) - but feeding it L/B and ROS from CFFDRS.
    return math.pi / (4.0 * length_to_breadth_at_time) * math.pow(fire_spread_distance, 2.0) / 10000.0


def get_fire_type(fuel_type: FuelTypeEnum, crown_fraction_burned: float) -> FireTypeEnum:
    """ Returns Fire Type (as FireTypeEnum) based on percentage Crown Fraction Burned (CFB).
    These definitions come from the Red Book (p.69).
    Abbreviations for fire types have been taken from the red book (p.9).

    CROWN FRACTION BURNED           TYPE OF FIRE                ABBREV.
    < 10%                           Surface fire                SUR
    10-89%                          Intermittent crown fire     IC
    > 90%                           Continuous crown fire       CC
    """
    if fuel_type == FuelTypeEnum.D1:
        # From red book "crown fires are not expected in deciduous fuel types but high intensity surface fires
        # can occur."
        return FireTypeEnum.SURFACE
    # crown fraction burnt is a floating point number from 0 to 1 inclusive.
    if crown_fraction_burned < 0.1:
        return FireTypeEnum.SURFACE
    if crown_fraction_burned < 0.9:
        return FireTypeEnum.INTERMITTENT_CROWN
    if crown_fraction_burned >= 0.9:
        return FireTypeEnum.CONTINUOUS_CROWN
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
    if last_observed_morning_rh_values is None:
        return None
    if daily_ffmc < critical_ffmc:
        logger.debug('Daily FFMC %s < critical FFMC %s', daily_ffmc, critical_ffmc)
        # Daily FFMC represents peak burning, so diurnal hourly FFMC will never be higher than daily FFMC
        # if daily FFMC < critical FFMC, station will never reach critical FFMC at any hour of the day
        return None
    # else daily_ffmc >= critical_ffmc
    logger.debug('Daily FFMC %s >= critical FFMC %s', daily_ffmc, critical_ffmc)
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


def get_critical_hours(
        target_hfi: int, fuel_type: FuelTypeEnum, percentage_conifer: float,
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
    logger.debug('Critical FFMC %s, resulting HFI %s; target HFI %s', critical_ffmc,
                 resulting_hfi, target_hfi)
    # Scenario 1 (resulting_hfi < target_hfi) - will happen when it's impossible to get
    # a HFI value large enough to >= target_hfi, because FFMC influences the HFI value,
    # and FFMC has an upper bound of 101. So basically, in this scenario the resulting_hfi
    # would equal the resulting HFI when FFMC is set to 101.
    if critical_ffmc >= 100.9 and resulting_hfi < target_hfi:
        logger.debug('No critical hours for HFI %s. Critical FFMC %s has HFI %s',
                     target_hfi, critical_ffmc, resulting_hfi)
        return None
    # Scenario 2: the HFI is always >= target_hfi, even when FFMC = 0. In this case, all hours
    # of the day will be critical hours.
    if critical_ffmc == 0.0 and resulting_hfi >= target_hfi:
        logger.info('All hours critical for HFI %s. FFMC %s has HFI %s',
                    target_hfi, critical_ffmc, resulting_hfi)
        return CriticalHoursHFI(start=13.0, end=7.0)
    # Scenario 3: there is a critical_ffmc between (0, 101) that corresponds to
    # resulting_hfi >= target_hfi. Now have to determine what hours of the day (if any)
    # will see hourly FFMC (adjusted according to diurnal curve) >= critical_ffmc.
    critical_hours_start = get_critical_hours_start(
        critical_ffmc, daily_ffmc, prev_daily_ffmc, last_observed_morning_rh_values)
    if critical_hours_start is None:
        return None
    critical_hours_end = get_critical_hours_end(
        critical_ffmc, daily_ffmc, critical_hours_start)

    return CriticalHoursHFI(start=critical_hours_start, end=critical_hours_end)


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


class FireBehaviourPrediction:
    """ Structure for storing fire behaviour prediction data. """

    def __init__(self, ros: float,
                 hfi: float, intensity_group,
                 sixty_minute_fire_size: float,
                 fire_type) -> None:
        self.ros = ros
        self.hfi = hfi
        self.intensity_group = intensity_group
        self.sixty_minute_fire_size = sixty_minute_fire_size
        self.fire_type = fire_type


def calculate_intensity_group(hfi: float) -> int:
    """ Returns a 1-5 integer value indicating Intensity Group based on HFI.
    Intensity groupings are:

    HFI             IG
    0-499            1
    500-999          2
    1000-1999        3
    2000-3999        4
    4000+            5
    """
    if hfi < 500:
        return 1
    if hfi < 1000:
        return 2
    if hfi < 2000:
        return 3
    if hfi < 4000:
        return 4
    return 5


def calculate_fire_behaviour_prediction_using_cffdrs(
        latitude: float,
        longitude: float,
        elevation: float,
        fuel_type: FuelTypeEnum,
        bui: float,
        ffmc: float,
        cc: float,
        pc: float,
        wind_speed: float,
        isi: float,
        pdf: float,
        cbh: float,
        cfl: float):
    """ Calculates fire behaviour prediction using CFFDRS. """
    # Set default values in case the calculation fails (likely due to missing data)
    fmc = cffdrs.foliar_moisture_content(latitude, longitude, elevation, get_julian_date_now())
    sfc = cffdrs.surface_fuel_consumption(fuel_type, bui, ffmc, pc)

    ros = cffdrs.rate_of_spread(FuelTypeEnum[fuel_type], isi, bui, fmc, sfc, pc=pc,
                                cc=cc,
                                pdf=pdf,
                                cbh=cbh)
    if sfc is not None:
        cfb = calculate_cfb(FuelTypeEnum[fuel_type], fmc, sfc, ros, cbh)

    if ros is not None and cfb is not None and cfl is not None:
        hfi = cffdrs.head_fire_intensity(fuel_type=FuelTypeEnum[fuel_type],
                                         percentage_conifer=pc,
                                         percentage_dead_balsam_fir=pdf,
                                         ros=ros, cfb=cfb, cfl=cfl, sfc=sfc)

    lb_ratio = cffdrs.length_to_breadth_ratio(FuelTypeEnum[fuel_type], wind_speed)
    wsv = cffdrs.calculate_wind_speed(FuelTypeEnum[fuel_type],
                                      ffmc=ffmc,
                                      bui=bui,
                                      ws=wind_speed,
                                      fmc=fmc,
                                      sfc=sfc,
                                      pc=pc,
                                      cc=cc,
                                      pdf=pdf,
                                      cbh=cbh,
                                      isi=isi)

    bros = cffdrs.back_rate_of_spread(FuelTypeEnum[fuel_type],
                                      ffmc=ffmc,
                                      bui=bui,
                                      wsv=wsv,
                                      fmc=fmc, sfc=sfc,
                                      pc=pc,
                                      cc=cc,
                                      pdf=pdf,
                                      cbh=cbh)

    sixty_minute_fire_size = get_fire_size(FuelTypeEnum[fuel_type], ros, bros, 60, cfb, lb_ratio)

    fire_type = get_fire_type(FuelTypeEnum[fuel_type], crown_fraction_burned=cfb)

    if hfi is not None:
        intensity_group = calculate_intensity_group(hfi)

    fire_behaviour_prediction = FireBehaviourPrediction(ros=ros, hfi=hfi, intensity_group=intensity_group,
                                                        sixty_minute_fire_size=sixty_minute_fire_size,
                                                        fire_type=fire_type)
    return fire_behaviour_prediction


def calculate_fire_behaviour_prediction_using_c7b(latitude: float,
                                                  longitude: float,
                                                  elevation: float,
                                                  ffmc: float,
                                                  bui: float,
                                                  wind_speed: float,
                                                  cc: float,
                                                  cbh: float,
                                                  cfl: float):
    """ Calculates fire behaviour prediction using C7B. """
    if cc is None:
        raise FireBehaviourPredictionInputError("CC is required for C7B calculation.")

    ros = c7b.rate_of_spread(ffmc=ffmc, bui=bui, wind_speed=wind_speed, percentage_slope=0.0, cc=cc)

    fmc = cffdrs.foliar_moisture_content(latitude, longitude, elevation, get_julian_date_now())

    sfc = cffdrs.surface_fuel_consumption(fuel_type=FuelTypeEnum.C7, bui=bui, ffmc=ffmc, pc=None)
    cfb = cffdrs.crown_fraction_burned(fuel_type=FuelTypeEnum.C7, fmc=fmc,
                                       sfc=sfc, ros=ros, cbh=cbh)

    hfi = cffdrs.head_fire_intensity(fuel_type=FuelTypeEnum.C7,
                                     percentage_conifer=None,
                                     percentage_dead_balsam_fir=None,
                                     ros=ros, cfb=cfb, cfl=cfl, sfc=sfc)

    fire_type = get_fire_type(FuelTypeEnum.C7B, cfb)

    intensity_group = calculate_intensity_group(hfi)

    # TODO: not required for HFI, but for FireBat - we need to calculate 60 minute fire size, which
    # will take a fair amount of peeking at the math.
    # Some of the math in the c7b.rate_of_spread can be extracted, and the standard cffdrs math used.
    fire_behaviour_prediction = FireBehaviourPrediction(
        ros=ros,
        hfi=hfi,
        intensity_group=intensity_group,
        sixty_minute_fire_size=None,
        fire_type=fire_type)

    return fire_behaviour_prediction


def calculate_fire_behaviour_prediction(latitude: float,
                                        longitude: float, elevation: float,
                                        fuel_type: FuelTypeEnum,
                                        bui: float, ffmc: float, wind_speed: float,
                                        cc: float,
                                        pc: float,
                                        isi: float, pdf: float, cbh: float, cfl: float):
    """ Calculate the fire behaviour prediction. """
    if wind_speed is None:
        raise FireBehaviourPredictionInputError('Wind speed must be specified')
    if bui is None:
        raise FireBehaviourPredictionInputError('BUI is required')
    if ffmc is None:
        raise FireBehaviourPredictionInputError('FFMC is required')
    if cc is None and is_grass_fuel_type(fuel_type):
        raise FireBehaviourPredictionInputError('Grass Cure must be specified for grass fuel types')
    if fuel_type == FuelTypeEnum.C7B:
        return calculate_fire_behaviour_prediction_using_c7b(
            latitude=latitude,
            longitude=longitude,
            elevation=elevation,
            ffmc=ffmc,
            bui=bui,
            wind_speed=wind_speed,
            cc=cc,
            cbh=cbh,
            cfl=cfl)
    return calculate_fire_behaviour_prediction_using_cffdrs(
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
        fuel_type=fuel_type,
        bui=bui,
        ffmc=ffmc,
        cc=cc,
        pc=pc,
        wind_speed=wind_speed,
        isi=isi,
        pdf=pdf,
        cbh=cbh,
        cfl=cfl)
