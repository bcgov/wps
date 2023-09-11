import pytest
from app.fire_behaviour.fuel_types import FuelTypeEnum
from app.fire_behaviour.critical_hours import (get_afternoon_overnight_diurnal_ffmc, get_critical_hours_end,
                                               get_morning_diurnal_ffmc,
                                               get_critical_hours,
                                               get_ffmc_for_target_hfi)
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
    assert crit_hours_4000 == CriticalHoursHFI(start=7.00, end=15.00)


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
    assert crit_hours_4000 == CriticalHoursHFI(start=7.00, end=15.00)


def test_critical_hours_4000_high_rh():
    """ A high daily FFMC with consistently high morning RH hourly values for target hfi of 4000 """
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
                                         last_observed_morning_rh_values={7.0: 88.0, 8.0: 88.0, 9.0: 88.0, 10.0: 88.0, 11.0: 88.0, 12.0: 88.0})
    assert crit_hours_4000 == CriticalHoursHFI(start=10.00, end=15.00)


def test_critical_hours_10000_high_rh():
    """ A high daily FFMC with consistently high morning RH hourly values for target hfi of 10000 """
    crit_hours_4000 = get_critical_hours(target_hfi=10000,
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
                                         last_observed_morning_rh_values={7.0: 88.0, 8.0: 88.0, 9.0: 88.0, 10.0: 88.0, 11.0: 88.0, 12.0: 88.0})
    assert crit_hours_4000 == CriticalHoursHFI(start=13.00, end=21.00)


def test_critical_hours_low_ffmc_4000():
    """ A low daily ffmc produces no critical hours for target HFI 4000 """
    crit_hours_4000 = get_critical_hours(target_hfi=4000,
                                         fuel_type=FuelTypeEnum.C2,
                                         percentage_conifer=100,
                                         percentage_dead_balsam_fir=None,
                                         bui=148.558,
                                         grass_cure=None,
                                         crown_base_height=3.0,
                                         daily_ffmc=55,
                                         fmc=120,
                                         cfb=0.9615453070844759,
                                         cfl=0.8,
                                         wind_speed=10.3,
                                         prev_daily_ffmc=55,
                                         last_observed_morning_rh_values={7.0: 54.0, 8.0: 47.0, 9.0: 46.0, 10.0: 45.0, 11.0: 44.0, 12.0: 38.0})
    assert crit_hours_4000 is None


def test_critical_hours_low_ffmc_10000():
    """ A low daily ffmc produces no critical hours for target HFI 10000 """
    crit_hours_10000 = get_critical_hours(target_hfi=10000,
                                          fuel_type=FuelTypeEnum.C2,
                                          percentage_conifer=100,
                                          percentage_dead_balsam_fir=None,
                                          bui=148.558,
                                          grass_cure=None,
                                          crown_base_height=3.0,
                                          daily_ffmc=55,
                                          fmc=120,
                                          cfb=0.9615453070844759,
                                          cfl=0.8,
                                          wind_speed=10.3,
                                          prev_daily_ffmc=55,
                                          last_observed_morning_rh_values={7.0: 54.0, 8.0: 47.0, 9.0: 46.0, 10.0: 45.0, 11.0: 44.0, 12.0: 38.0})
    assert crit_hours_10000 is None


def test_overnight_diurnal():
    result = get_afternoon_overnight_diurnal_ffmc(hour_of_interest=13, daily_ffmc=55)
    assert result == 48.2


def test_morning_diurnal():
    result = get_morning_diurnal_ffmc(hour_of_interest=7, prev_day_daily_ffmc=55, hourly_rh=67)
    assert result == 56.9


def test_get_ffmc_for_target_hfi():
    " Smoke test to make sure 10000 target hfi produces larger outputs than the 4000 target hfi"
    (ffmc_4000, hfi_4000) = get_ffmc_for_target_hfi(fuel_type=FuelTypeEnum.C2,
                                                    percentage_conifer=50,
                                                    percentage_dead_balsam_fir=0,
                                                    bui=65,
                                                    wind_speed=15,
                                                    grass_cure=0,
                                                    crown_base_height=3,
                                                    ffmc=50,
                                                    fmc=97,
                                                    cfb=50,
                                                    cfl=10,
                                                    target_hfi=4000)

    (ffmc_10000, hfi_10000) = get_ffmc_for_target_hfi(fuel_type=FuelTypeEnum.C2,
                                                      percentage_conifer=50,
                                                      percentage_dead_balsam_fir=0,
                                                      bui=65,
                                                      wind_speed=15,
                                                      grass_cure=0,
                                                      crown_base_height=3,
                                                      ffmc=50,
                                                      fmc=97,
                                                      cfb=50,
                                                      cfl=10,
                                                      target_hfi=10000)

    assert hfi_10000 > hfi_4000
    assert ffmc_10000 > ffmc_4000


@pytest.mark.parametrize(
    "daily_ffmc, prev_daily_ffmc, last_observed_morning_rh_values, expected_start, expected_end",
    [
        # high daily ffmc, high previous daily ffmc, mid range rh values
        (90, 90, {7.0: 54.0, 8.0: 47.0, 9.0: 46.0, 10.0: 45.0, 11.0: 44.0, 12.0: 38.0}, 11.00, 22.00),
        # high daily ffmc, high previous daily ffmc, high range rh values
        (90, 90, {7.0: 88.0, 8.0: 88.0, 9.0: 88.0, 10.0: 88.0, 11.0: 88.0, 12.0: 88.0}, 12.00, 22.00),

        # higher daily ffmc, higher previous daily ffmc, mid range rh values
        (92, 92, {7.0: 54.0, 8.0: 47.0, 9.0: 46.0, 10.0: 45.0, 11.0: 44.0, 12.0: 38.0}, 9.00, 0.00),
        # higher daily ffmc, higher previous daily ffmc, high range rh values
        (92, 92, {7.0: 88.0, 8.0: 88.0, 9.0: 88.0, 10.0: 88.0, 11.0: 88.0, 12.0: 88.0}, 12.00, 0.00),

    ],
)
def test_critical_hours_4000_high_ffmc(daily_ffmc, prev_daily_ffmc, last_observed_morning_rh_values, expected_start, expected_end):
    crit_hours_4000 = get_critical_hours(target_hfi=4000,
                                         fuel_type=FuelTypeEnum.C2,
                                         percentage_conifer=100,
                                         percentage_dead_balsam_fir=None,
                                         bui=148.558,
                                         grass_cure=None,
                                         crown_base_height=3.0,
                                         daily_ffmc=daily_ffmc,
                                         fmc=120,
                                         cfb=0.9615453070844759,
                                         cfl=0.8,
                                         wind_speed=10.3,
                                         prev_daily_ffmc=prev_daily_ffmc,
                                         last_observed_morning_rh_values=last_observed_morning_rh_values)
    assert crit_hours_4000.start == expected_start
    assert crit_hours_4000.end == expected_end


@pytest.mark.parametrize(
    "daily_ffmc, prev_daily_ffmc, last_observed_morning_rh_values, expected_start, expected_end",
    [
        # high daily ffmc, high previous daily ffmc, mid range rh values
        (90, 90, {7.0: 54.0, 8.0: 47.0, 9.0: 46.0, 10.0: 45.0, 11.0: 44.0, 12.0: 38.0}, 14.00, 19.00),
        # high daily ffmc, high previous daily ffmc, high range rh values
        (90, 90, {7.0: 88.0, 8.0: 88.0, 9.0: 88.0, 10.0: 88.0, 11.0: 88.0, 12.0: 88.0}, 14.00, 19.00),

        # higher daily ffmc, higher previous daily ffmc, mid range rh values
        (92, 92, {7.0: 54.0, 8.0: 47.0, 9.0: 46.0, 10.0: 45.0, 11.0: 44.0, 12.0: 38.0}, 12.00, 21.00),
        # higher daily ffmc, higher previous daily ffmc, high range rh values
        (92, 92, {7.0: 88.0, 8.0: 88.0, 9.0: 88.0, 10.0: 88.0, 11.0: 88.0, 12.0: 88.0}, 13.00, 21.00),

    ],
)
def test_critical_hours_10000_high_ffmc(daily_ffmc, prev_daily_ffmc, last_observed_morning_rh_values, expected_start, expected_end):
    crit_hours_4000 = get_critical_hours(target_hfi=10000,
                                         fuel_type=FuelTypeEnum.C2,
                                         percentage_conifer=100,
                                         percentage_dead_balsam_fir=None,
                                         bui=148.558,
                                         grass_cure=None,
                                         crown_base_height=3.0,
                                         daily_ffmc=daily_ffmc,
                                         fmc=120,
                                         cfb=0.9615453070844759,
                                         cfl=0.8,
                                         wind_speed=10.3,
                                         prev_daily_ffmc=prev_daily_ffmc,
                                         last_observed_morning_rh_values=last_observed_morning_rh_values)
    assert crit_hours_4000.start == expected_start
    assert crit_hours_4000.end == expected_end


@pytest.mark.parametrize(
    "daily_ffmc, prev_daily_ffmc, last_observed_morning_rh_values",
    [
        # low daily ffmc, low previous daily ffmc, mid range rh values
        (50, 50, {7.0: 54.0, 8.0: 47.0, 9.0: 46.0, 10.0: 45.0, 11.0: 44.0, 12.0: 38.0}),
        # low daily ffmc, low previous daily ffmc, high range rh values
        (50, 50, {7.0: 88.0, 8.0: 88.0, 9.0: 88.0, 10.0: 88.0, 11.0: 88.0, 12.0: 88.0}),

        # higher daily ffmc, higher previous daily ffmc, mid range rh values
        (30, 30, {7.0: 54.0, 8.0: 47.0, 9.0: 46.0, 10.0: 45.0, 11.0: 44.0, 12.0: 38.0}),
        # higher daily ffmc, higher previous daily ffmc, high range rh values
        (30, 30, {7.0: 88.0, 8.0: 88.0, 9.0: 88.0, 10.0: 88.0, 11.0: 88.0, 12.0: 88.0}),

    ],
)
def test_critical_hours_4000_low_ffmc(daily_ffmc, prev_daily_ffmc, last_observed_morning_rh_values):
    crit_hours_4000 = get_critical_hours(target_hfi=4000,
                                         fuel_type=FuelTypeEnum.C2,
                                         percentage_conifer=100,
                                         percentage_dead_balsam_fir=None,
                                         bui=148.558,
                                         grass_cure=None,
                                         crown_base_height=3.0,
                                         daily_ffmc=daily_ffmc,
                                         fmc=120,
                                         cfb=0.9615453070844759,
                                         cfl=0.8,
                                         wind_speed=10.3,
                                         prev_daily_ffmc=prev_daily_ffmc,
                                         last_observed_morning_rh_values=last_observed_morning_rh_values)
    assert crit_hours_4000 is None


@pytest.mark.parametrize(
    "daily_ffmc, prev_daily_ffmc, last_observed_morning_rh_values",
    [
        # low daily ffmc, low previous daily ffmc, mid range rh values
        (50, 50, {7.0: 54.0, 8.0: 47.0, 9.0: 46.0, 10.0: 45.0, 11.0: 44.0, 12.0: 38.0}),
        # low daily ffmc, low previous daily ffmc, high range rh values
        (50, 50, {7.0: 88.0, 8.0: 88.0, 9.0: 88.0, 10.0: 88.0, 11.0: 88.0, 12.0: 88.0}),

        # higher daily ffmc, higher previous daily ffmc, mid range rh values
        (30, 30, {7.0: 54.0, 8.0: 47.0, 9.0: 46.0, 10.0: 45.0, 11.0: 44.0, 12.0: 38.0}),
        # higher daily ffmc, higher previous daily ffmc, high range rh values
        (30, 30, {7.0: 88.0, 8.0: 88.0, 9.0: 88.0, 10.0: 88.0, 11.0: 88.0, 12.0: 88.0}),

    ],
)
def test_critical_hours_10000_low_ffmc(daily_ffmc, prev_daily_ffmc, last_observed_morning_rh_values):
    crit_hours_4000 = get_critical_hours(target_hfi=10000,
                                         fuel_type=FuelTypeEnum.C2,
                                         percentage_conifer=100,
                                         percentage_dead_balsam_fir=None,
                                         bui=148.558,
                                         grass_cure=None,
                                         crown_base_height=3.0,
                                         daily_ffmc=daily_ffmc,
                                         fmc=120,
                                         cfb=0.9615453070844759,
                                         cfl=0.8,
                                         wind_speed=10.3,
                                         prev_daily_ffmc=prev_daily_ffmc,
                                         last_observed_morning_rh_values=last_observed_morning_rh_values)
    assert crit_hours_4000 is None


def test_critical_hours_end_exceeds_day_in_total_hours():
    get_critical_hours_end(critical_ffmc=74.51679687499995,
                           solar_noon_ffmc=94.8,
                           critical_hour_start=7.0)
