import pytest
import logging
from datetime import date
from wps_shared.fuel_types import FuelTypeEnum
from wps_shared.utils.time import get_hour_20_from_date
from app.fire_behaviour.advisory import calculate_fire_behaviour_advisory, FBACalculatorWeatherStation
from app.utils.redapp import FBPCalculateStatisticsCOM
from app.tests.fba_calc import check_metric, acceptable_margin_of_error, fire_size_acceptable_margin_of_error

logger = logging.getLogger(__name__)

# C1 Notes:
#
# C1 ROS in CFFDRS is correct (Based on investigation, the result differs from REDapp slightly
# but the way we call CFFDRS is correct.)
# C1 CFB requires the date of minimum foliar moisture content to be set to 144 to match the REDapp
# result.
# C1 in the coastal spreadsheet is wrong.
#
# C3 redapp error margin is off
# C6 The redapp error margin is horrible (71%-80%)! This must be improved!
# M1 The redapp error margin is HUGE!
# M2 The redapp error margin is HUGE!
# M4 Redapp margin bad.
# O1A Spreadsheet bad
# O1B Spreadsheet bad
# Current target for margin of error: 1% (or 0.01)

# one_hr_em :- 1 Hour Error Margin
# cfb_em :- Crown Fraction Burned Error Margin
# hfi_em :- Head Fire Intensity Error Margin

@pytest.mark.parametrize(
    "fuel_type,elevation,latitude,longitude,time_of_interest,wind_speed,wind_direction,percentage_conifer,percentage_dead_balsam_fir,grass_cure,crown_base_height,isi,bui,ffmc,dmc,dc,one_hr_em,ros_em,hfi_em,cfb_em",
    [
        ("C1", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 100, 0, 0, 2, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("C2", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 100, None, None, 3, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("C3", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 100, None, None, 8, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.02),
        ("C3", 3244, 55.207218202444906, -128.73536255317552, date.fromisoformat("2021-05-21"), 23.835537134445126, 168.4979596024838, 100.0, None, None, 8.0, 13.74041206802971, 55.2112620090575, 89.7461720614907, 33.22303813883521, 408.17004615391113, 0.01, 0.01, 0.01, 0.01),
        ("C3",3075,49.002377849288145,-129.53731237443654,date.fromisoformat("2021-02-10"),17.3906100267642,163.34053427851433,100.0,None,None,8.0,14.132196449385695,66.1696880962494,92.22387770168902,45.65846482284549,300.351667830179,0.14,0.01,0.05,0.08),
        ("C4", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 100, None, None, 4, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("C5", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 100, None, None, 18, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("C6", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 100, None, None, 7, 11.5, 186.8, 94.8, 126.1, 900.3, 0.02, 0.01, 0.01, 0.01),
        ("C6", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 100, None, None, 2, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("C7", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 100, None, None, 10, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("D1", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 100, None, None, None, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("M1", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 75, None, None, 6, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("M1", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 50, None, None, 6, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("M1", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 25, None, None, 6, 11.5, 186.8, 94.8, 126.1, 900.3, 0.39, 0.01, 0.07, 0.15),
        ("M2", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 75, None, None, 6, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("M2", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 50, None, None, 6, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("M2", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, 25, None, None, 6, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("M3", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, 30, None, 6, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("M3", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, 60, None, 6, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("M3", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, 100, None, 6, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("M4", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, 30, None, 6, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("M4", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, 60, None, 6, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("M4", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, 100, None, 6, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("O1A", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, None, 25, None, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("O1A", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, None, 50, None, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("O1A", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, None, 100, None, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("O1B", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, None, 25, None, 11.5, 186.8, 94.8, 126.1, 900.3, 0.12, 0.01, 0.01, 0.01),
        ("O1B", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, None, 50, None, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("O1B", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, None, 100, None, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("S1", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, None, None, None, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("S2", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, None, None, None, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01),
        ("S3", 780, 50.6733333, -120.4816667, date.fromisoformat("2021-07-12"), 6.2, 3, None, None, None, None, 11.5, 186.8, 94.8, 126.1, 900.3, 0.01, 0.01, 0.01, 0.01)
    ],
)
@pytest.mark.skip(reason="Only used for initial validation of FireCalc and REDapp")
def test_redapp_vs_fba(
    fuel_type,
    elevation,
    latitude,
    longitude,
    time_of_interest,
    wind_speed,
    wind_direction,
    percentage_conifer,
    percentage_dead_balsam_fir,
    grass_cure,
    crown_base_height,
    isi,
    bui,
    ffmc,
    dmc,
    dc,
    one_hr_em,
    ros_em,
    hfi_em,
    cfb_em,
):
    # get python result:
    python_input = FBACalculatorWeatherStation(
        elevation=elevation,
        fuel_type=FuelTypeEnum[fuel_type],
        time_of_interest=time_of_interest,
        percentage_conifer=percentage_conifer,
        percentage_dead_balsam_fir=percentage_dead_balsam_fir,
        grass_cure=grass_cure,
        crown_base_height=crown_base_height,
        crown_fuel_load=None,
        lat=latitude,
        long=longitude,
        bui=bui,
        ffmc=ffmc,
        isi=isi,
        fwi=None,
        wind_speed=wind_speed,
        wind_direction=wind_direction,
        temperature=20.0,  # temporary fix so tests don't break
        relative_humidity=20.0,
        precipitation=2.0,
        status="Forecasted",
        prev_day_daily_ffmc=90.0,
        last_observed_morning_rh_values={7.0: 61.0, 8.0: 54.0, 9.0: 43.0, 10.0: 38.0, 11.0: 34.0, 12.0: 23.0},
    )
    python_fba = calculate_fire_behaviour_advisory(python_input)
    # NOTE: REDapp has a ros_eq and a ros_t ;
    # assumptions:
    # ros_eq == ROScalc
    # ros_t  == ROStcalc
    # get REDapp result from java:
    java_fbp = FBPCalculateStatisticsCOM(
        elevation=elevation,
        latitude=latitude,
        longitude=longitude,
        time_of_interest=get_hour_20_from_date(time_of_interest),
        fuel_type=fuel_type,
        ffmc=ffmc,
        dmc=dmc,
        dc=dc,
        bui=bui,
        wind_speed=wind_speed,
        wind_direction=wind_direction,
        percentage_conifer=percentage_conifer,
        percentage_dead_balsam_fir=percentage_dead_balsam_fir,
        grass_cure=grass_cure,
        crown_base_height=crown_base_height,
    )
    check_metric("ROS", fuel_type, python_fba.ros, java_fbp.ros_eq, ros_em, "REDapp")
    check_metric('ROS_t', fuel_type, python_fba.ros_t, java_fbp.ros_t, acceptable_margin_of_error,"REDapp")
    check_metric('CFB', fuel_type, python_fba.cfb, java_fbp.cfb / 100.0, cfb_em, "REDapp") # CFFDRS gives cfb as a fraction
    check_metric('CFB_t', fuel_type, python_fba.cfb_t, java_fbp.cfb / 100.0, cfb_em, "REDapp") # CFFDRS gives cfb as a fraction
    check_metric('HFI', fuel_type, python_fba.hfi, java_fbp.hfi, hfi_em, "REDapp")
    check_metric('HFI_t', fuel_type, python_fba.hfi_t, java_fbp.hfi, acceptable_margin_of_error, "REDapp")
    check_metric('1 HR Size', fuel_type, python_fba.sixty_minute_fire_size, java_fbp.area, one_hr_em, "REDapp")
    check_metric('1 HR Size t', fuel_type, python_fba.sixty_minute_fire_size_t, java_fbp.area, fire_size_acceptable_margin_of_error, "REDapp")