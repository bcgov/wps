""" Code relating to fire behaviour advisories """

from datetime import date
from typing import Optional
from app.fire_behaviour import cffdrs
from app.fire_behaviour.fuel_types import FUEL_TYPE_DEFAULTS, FuelTypeEnum
from app.fire_behaviour.prediction import (
    FireTypeEnum, calculate_cfb, get_approx_flame_length, get_critical_hours, get_fire_size, get_fire_type)
from app.schemas.fba_calc import CriticalHoursHFI
from app.utils.time import get_hour_20_from_date, get_julian_date


class FBACalculatorWeatherStation():  # pylint: disable=too-many-instance-attributes
    """ Inputs for Fire Behaviour Advisory Calculator """

    def __init__(self,  # pylint: disable=too-many-arguments, too-many-locals
                 elevation: int, fuel_type: FuelTypeEnum,
                 time_of_interest: date, percentage_conifer: float,
                 percentage_dead_balsam_fir: float, grass_cure: float,
                 crown_base_height: int, crown_fuel_load: Optional[float], lat: float, long: float,
                 bui: float, ffmc: float, isi: float, fwi: float, wind_speed: float, wind_direction: float,
                 temperature: float, relative_humidity: float, precipitation: float, status: str,
                 prev_day_daily_ffmc: float, last_observed_morning_rh_values: dict):
        self.elevation = elevation
        self.fuel_type = fuel_type
        self.time_of_interest = time_of_interest
        self.percentage_conifer = percentage_conifer
        self.percentage_dead_balsam_fir = percentage_dead_balsam_fir
        self.grass_cure = grass_cure
        self.crown_base_height = crown_base_height
        # not many people know/care about the crown fuel load, so we can fill this out with default
        # values if set to None.
        self.crown_fuel_load = crown_fuel_load
        self.lat = lat
        self.long = long
        self.bui = bui
        self.ffmc = ffmc
        self.isi = isi
        self.fwi = fwi
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
        self.temperature = temperature
        self.relative_humidity = relative_humidity
        self.precipitation = precipitation
        self.status = status
        self.prev_day_daily_ffmc = prev_day_daily_ffmc
        self.last_observed_morning_rh_values = last_observed_morning_rh_values

    def __str__(self) -> str:
        return f"lat {self.lat}, long {self.long}, elevation {self.elevation}, fuel_type {self.fuel_type}, \
            time_of_interest {self.time_of_interest}, percentage_conifer {self.percentage_conifer},\
            percentage_dead_balsam_fir {self.percentage_dead_balsam_fir}, grass_cure {self.grass_cure},\
            crown_base_height {self.crown_base_height}, crown_fuel_load {self.crown_fuel_load}, bui {self.bui},\
            ffmc {self.ffmc}, isi {self.isi}, fwi {self.fwi} prev_day_daily_ffmc {self.prev_day_daily_ffmc},\
            wind_speed {self.wind_speed}, temperature {self.temperature},\
            relative_humidity {self.relative_humidity}, precipitation {self.precipitation},\
            status {self.status}"


class FireBehaviourAdvisory():  # pylint: disable=too-many-instance-attributes
    """ Class containing the results of the fire behaviour advisory calculation. """

    def __init__(self,  # pylint: disable=too-many-arguments
                 hfi: float, ros: float, fire_type: FireTypeEnum, cfb: float, flame_length: float,
                 sixty_minute_fire_size: float, thirty_minute_fire_size: float,
                 critical_hours_hfi_4000: Optional[CriticalHoursHFI],
                 critical_hours_hfi_10000: Optional[CriticalHoursHFI],
                 hfi_t: Optional[float],
                 ros_t: Optional[float],
                 cfb_t: Optional[float],
                 sixty_minute_fire_size_t: Optional[float]):
        self.hfi = hfi
        self.ros = ros
        self.fire_type = fire_type
        self.cfb = cfb
        self.flame_length = flame_length
        self.sixty_minute_fire_size = sixty_minute_fire_size
        self.thirty_minute_fire_size = thirty_minute_fire_size
        self.critical_hours_hfi_4000 = critical_hours_hfi_4000
        self.critical_hours_hfi_10000 = critical_hours_hfi_10000
        # hfi vs. hfi_t ?
        # *_t is calculated using ros_t, which is rate of spread since time of ignition.
        # * is calculated using a rate of spread calculation that does not assume an ignition time.
        self.hfi_t = hfi_t
        self.ros_t = ros_t
        self.cfb_t = cfb_t
        self.sixty_minute_fire_size_t = sixty_minute_fire_size_t


def calculate_fire_behaviour_advisory(station: FBACalculatorWeatherStation) -> FireBehaviourAdvisory:
    """ Transform from the raw daily json object returned by wf1, to our fba_calc.StationResponse object.
    """
    # pylint: disable=too-many-locals
    # time of interest will be the same for all stations.
    time_of_interest = get_hour_20_from_date(station.time_of_interest)

    fmc = cffdrs.foliar_moisture_content(station.lat, station.long, station.elevation,
                                         get_julian_date(time_of_interest))
    sfc = cffdrs.surface_fuel_consumption(station.fuel_type, station.bui,
                                          station.ffmc, station.percentage_conifer)
    lb_ratio = cffdrs.length_to_breadth_ratio(station.fuel_type, station.wind_speed)
    ros = cffdrs.rate_of_spread(station.fuel_type, isi=station.isi, bui=station.bui, fmc=fmc, sfc=sfc,
                                pc=station.percentage_conifer,
                                cc=station.grass_cure,
                                pdf=station.percentage_dead_balsam_fir,
                                cbh=station.crown_base_height)
    cfb = calculate_cfb(station.fuel_type, fmc, sfc, ros, station.crown_base_height)

    # Calculate rate of spread assuming 60 minutes since ignition.
    ros_t = cffdrs.rate_of_spread_t(
        fuel_type=station.fuel_type,
        ros_eq=ros,
        minutes_since_ignition=60,
        cfb=cfb)
    cfb_t = calculate_cfb(station.fuel_type, fmc, sfc, ros_t, station.crown_base_height)

    # Get the default crown fuel load, if none specified.
    if station.crown_fuel_load is None:
        cfl = FUEL_TYPE_DEFAULTS[station.fuel_type].get('CFL', None)
    else:
        cfl = station.crown_fuel_load

    hfi = cffdrs.head_fire_intensity(fuel_type=station.fuel_type,
                                     percentage_conifer=station.percentage_conifer,
                                     percentage_dead_balsam_fir=station.percentage_dead_balsam_fir,
                                     ros=ros, cfb=cfb, cfl=cfl, sfc=sfc)
    hfi_t = cffdrs.head_fire_intensity(fuel_type=station.fuel_type,
                                       percentage_conifer=station.percentage_conifer,
                                       percentage_dead_balsam_fir=station.percentage_dead_balsam_fir,
                                       ros=ros_t, cfb=cfb_t, cfl=cfl, sfc=sfc)
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

    wsv = cffdrs.calculate_wind_speed(fuel_type=station.fuel_type, ffmc=station.ffmc,
                                      bui=station.bui, ws=station.wind_speed,
                                      fmc=fmc, sfc=sfc,
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
    sixty_minute_fire_size_t = get_fire_size(station.fuel_type, ros_t, bros, 60, cfb_t, lb_ratio)
    thirty_minute_fire_size = get_fire_size(station.fuel_type, ros, bros, 30, cfb, lb_ratio)

    return FireBehaviourAdvisory(
        hfi=hfi, ros=ros, fire_type=fire_type, cfb=cfb, flame_length=flame_length,
        sixty_minute_fire_size=sixty_minute_fire_size,
        thirty_minute_fire_size=thirty_minute_fire_size,
        critical_hours_hfi_4000=critical_hours_4000,
        critical_hours_hfi_10000=critical_hours_10000,
        hfi_t=hfi_t, ros_t=ros_t, cfb_t=cfb_t, sixty_minute_fire_size_t=sixty_minute_fire_size_t)
