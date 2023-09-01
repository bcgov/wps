import logging
from app.fire_behaviour.afternoon_diurnal_ffmc import AfternoonDiurnalFFMCLookupTable
from app.fire_behaviour.c7b import rate_of_spread
from app.schemas.fba_calc import FuelTypeEnum
from app.schemas.fba_calc import CriticalHoursHFI
from app.fire_behaviour import cffdrs

logger = logging.getLogger(__name__)


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
    critical_ffmc, resulting_hfi = get_ffmc_for_target_hfi(
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
    experimental_sfc = cffdrs.surface_fuel_consumption(fuel_type, bui, experimental_ffmc, percentage_conifer)
    experimental_isi = cffdrs.initial_spread_index(experimental_ffmc, wind_speed)
    experimental_ros = cffdrs.rate_of_spread(fuel_type, experimental_isi, bui, fmc, experimental_sfc,
                                             percentage_conifer,
                                             grass_cure, percentage_dead_balsam_fir, crown_base_height)
    experimental_hfi = cffdrs.head_fire_intensity(fuel_type,
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
        experimental_isi = cffdrs.initial_spread_index(experimental_ffmc, wind_speed)
        experimental_sfc = cffdrs.surface_fuel_consumption(fuel_type, bui, experimental_ffmc, percentage_conifer)
        experimental_ros = rate_of_spread(fuel_type, experimental_isi, bui, fmc,
                                          experimental_sfc, percentage_conifer,
                                          grass_cure, percentage_dead_balsam_fir, crown_base_height)
        experimental_hfi = cffdrs.head_fire_intensity(fuel_type,
                                                      percentage_conifer,
                                                      percentage_dead_balsam_fir, experimental_ros,
                                                      cfb, cfl, experimental_sfc)
        error_hfi = (target_hfi - experimental_hfi) / target_hfi

    return (experimental_ffmc, experimental_hfi)


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


def get_afternoon_overnight_diurnal_ffmc(hour_of_interest: int, daily_ffmc: float):
    """ Returns the diurnal FFMC (an approximation) estimated for the given hour_of_interest,
    based on the daily_ffmc.
    Hour_of_interest should be expressed in PDT time zone, and can only be between the hours
    1300 and 0700 the next morning. Otherwise, must use different function.
    """
    return AfternoonDiurnalFFMCLookupTable.instance().get(daily_ffmc, hour_of_interest)


def get_morning_diurnal_ffmc(hour_of_interest: int, prev_day_daily_ffmc: float, hourly_rh: float):
    """ Returns the diurnal FFMC (an approximation) estimated for the given hour_of_interest,
    based on the estimated RH value for the hour_of_interest.
    """
    morning_df = AfternoonDiurnalFFMCLookupTable.instance().morning_df

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
