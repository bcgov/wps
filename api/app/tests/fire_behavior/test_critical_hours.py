from app.fire_behaviour.fuel_types import FuelTypeEnum
from app.fire_behaviour.critical_hours import get_afternoon_overnight_diurnal_ffmc, get_critical_hours
from app.schemas.fba_calc import CriticalHoursHFI


def test_critical_hours_4000():
    crit_hours_4000 = get_critical_hours(target_hfi=4000,
                                         fuel_type=FuelTypeEnum.C2,
                                         percentage_conifer=100,
                                         percentage_dead_balsam_fir=None,
                                         bui=148.558,
                                         grass_cure=None,
                                         crown_base_height=3.0,
                                         daily_ffmc=92.08498474903236,
                                         fmc=120,
                                         cfb=0.9615453070844759,
                                         cfl=0.8,
                                         wind_speed=10.3,
                                         prev_daily_ffmc=94.561,
                                         last_observed_morning_rh_values={7.0: 54.0, 8.0: 47.0, 9.0: 46.0, 10.0: 45.0, 11.0: 44.0, 12.0: 38.0})
    assert crit_hours_4000 == CriticalHoursHFI(start=7.00, end=0.00)


def test_critical_hours_4000_manual_different_cfb():
    crit_hours_4000 = get_critical_hours(target_hfi=4000,
                                         fuel_type=FuelTypeEnum.C2,
                                         percentage_conifer=100,
                                         percentage_dead_balsam_fir=None,
                                         bui=148.558,
                                         grass_cure=None,
                                         crown_base_height=3.0,
                                         daily_ffmc=92.08498474903236,
                                         fmc=120,
                                         cfb=0.9689270350996513,
                                         cfl=0.8,
                                         wind_speed=10.3,
                                         prev_daily_ffmc=94.561,
                                         last_observed_morning_rh_values={7.0: 54.0, 8.0: 47.0, 9.0: 46.0, 10.0: 45.0, 11.0: 44.0, 12.0: 38.0})
    assert crit_hours_4000 == CriticalHoursHFI(start=7.00, end=0.00)


def test_overnight_diurnal():
    get_afternoon_overnight_diurnal_ffmc()
