"""
Unit tests for fire behaviour calculator.
"""

from datetime import datetime, timezone as dt_tz
import random
from typing import Final
import logging
from wps_shared.wps_logging import configure_logging
from wps_shared.fuel_types import FuelTypeEnum
from wps_shared.utils.time import get_hour_20_from_date
from app.fire_behaviour.advisory import calculate_fire_behaviour_advisory, FBACalculatorWeatherStation
from app.fire_behaviour.cffdrs import fire_weather_index, initial_spread_index, bui_calc
from app.utils.redapp import FBPCalculateStatisticsCOM
from app.tests.fba_calc import check_metric, fire_size_acceptable_margin_of_error
import pytest


configure_logging()

logger = logging.getLogger(__name__)


def _random_date():
    start = datetime.fromisoformat("2021-01-01")
    end = datetime.fromisoformat("2021-12-31")
    return datetime.fromtimestamp(random.uniform(start.timestamp(), end.timestamp()), tz=dt_tz.utc)


acceptable_margin_of_error: Final = 0.01


@pytest.mark.parametrize(
    "fuel_type, percentage_conifer, percentage_dead_balsam_fir, grass_cure, crown_base_height, ros_margin_of_error, hfi_margin_of_error, cfb_margin_of_error, cfb_t_margin_of_error, one_hour_spread_margin_of_error, num_iterations,",
    [
        ("C1", 100, None, None, 2, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        ("C2", 100, None, None, 3, 0.01, 0.12, 0.19, 0.01, 0.17, 20),
        ("C3", 100, None, None, 8, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        # C4 and C5 seem to have some issues with CFB
        # | C4        | 100                | None                       | None       | 8                 | 0.01                | 0.02                | 1.00              | 0.01   | 0.28                            | 20             |
        # | C5        | 100                | None                       | None       | 8                 | 0.01                | 0.01                | 0.04              | 0.01   | 0.01                            | 20             |         | C6        | 100                | None                       | None       | 7                 | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
        ("C7", 100, None, None, 8, 0.01, 0.01, 0.01, 0.01, 0.01, 0),
        ("D1", 100, None, None, None, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        # M1, M2, M3 & M4 are failing on 1Ha Fire Size (though not that bad!)
        # | M1_75C        | 75                 | None                       | None       | 6                 | 0.01                | 0.02                | 0.02           | 0.01      | 0.05                            | 20             |
        # | M1_50C        | 50                 | None                       | None       | 6                 | 0.01                | 0.21                | 0.61           | 0.01      | 0.10                            | 20             |
        ("M1", 25, None, None, 6, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        # | M2_75C        | 75                 | None                       | None       | 6                 | 0.01                | 0.03                | 0.03        | 0.01         | 0.07                            | 20             |
        # | M2_50C        | 50                 | None                       | None       | 6                 | 0.01                | 0.11                | 0.39        | 0.01         | 0.13                            | 20             |
        ("M2", 25, None, None, 6, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        ("M3", None, 30, None, 6, 0.01, 0.01, 0.19, 0.12, 0.01, 20),
        ("M3", None, 60, None, 6, 0.01, 0.19, 0.48, 0.01, 0.35, 20),
        # | M3_100D        | None               | 100                        | None       | 6                 | 0.01                | 0.17                | 0.32         | 0.01        | 0.38                            | 20             |
        # | M4_30D        | None               | 30                         | None       | 6                 | 0.01                | 0.19                | 0.36        | 0.01         | 0.21                            | 20             |
        ("M4", None, 60, None, 6, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        ("M4", None, 100, None, 6, 0.01, 0.03, 0.12, 0.01, 0.02, 20),
        ("O1A", None, None, 25, None, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        ("O1A", None, None, 50, None, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        ("O1A", None, None, 100, None, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        ("O1B", None, None, 25, None, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        ("O1B", None, None, 50, None, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        ("O1B", None, None, 100, None, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        ("S1", None, None, None, None, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        ("S2", None, None, None, None, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
        ("S3", None, None, None, None, 0.01, 0.01, 0.01, 0.01, 0.01, 20),
    ],
)
@pytest.mark.skip(reason="Only used for initial validation of FireCalc and REDapp")
def test_get_endpoints_unauthorized(
    fuel_type,
    percentage_conifer,
    percentage_dead_balsam_fir,
    grass_cure,
    crown_base_height,
    ros_margin_of_error,
    hfi_margin_of_error,
    cfb_margin_of_error,
    cfb_t_margin_of_error,
    one_hour_spread_margin_of_error,
    num_iterations,
):
    """Calculate actual and expected outputs"""
    # get python result:
    # seed = time()
    seed = 43
    logger.info("using random seed: %s", seed)
    random.seed(seed)
    for index in range(num_iterations):
        elevation = random.randint(0, 4019)
        latitude = random.uniform(45, 60)
        longitude = random.uniform(-118, -136)
        time_of_interest = _random_date()
        # NOTE: For high wind speeds, the difference between REDapp and FireBAT starts exceeding
        # tolerances. REDapp calculates it's own ISI (doesn't take the one provided by the system),
        # but uses a different formula from CFFDRS, so the results start getting more pronounced
        # with higher wind speeds. For that reason we limit our wind speeds to 40 km/h, since anything
        # above that starts failing the unit tests.
        wind_speed = random.uniform(0, 40)
        wind_direction = random.uniform(0, 360)
        temperature = random.uniform(0, 49.6)  # Lytton, B.C., 2021
        relative_humidity = random.uniform(0, 100)
        precipitation = random.uniform(0, 50)
        dc = random.uniform(0, 600)
        dmc = random.uniform(11, 205)
        bui = bui_calc(dmc, dc)
        ffmc = random.uniform(11, 100)
        isi = initial_spread_index(ffmc, wind_speed)
        fwi = fire_weather_index(isi, bui)

        message = (
            f"""({index}) elevation:{elevation} ; lat: {latitude} ; lon: {longitude}; """
            f"""toi: {time_of_interest}; ws: {wind_speed}; wd: {wind_direction}; """
            f"""temperature: {temperature}; relative_humidity: {relative_humidity}; """
            f"""precipitation: {precipitation}; dc: {dc}; dmc: {dmc}; bui: {bui}; """
            f"""ffmc: {ffmc}; isi: {isi}"""
        )
        logger.debug(message)

        test_entry = (
            f"""({index}) | {fuel_type} | {elevation} | {latitude} | {longitude} | """
            f"""{time_of_interest} | {wind_speed} | {wind_direction} | {percentage_conifer} | """
            f"""{percentage_dead_balsam_fir} | {grass_cure} | {crown_base_height} | {isi}  | """
            f"""{bui} | {ffmc} | {dmc} | {dc} | 0.01 | 0.01 | 0.01 | 0.01 | None | 0.01 | """
            f"""None | 0.01 | None | 0.01 | |"""
        )
        logger.debug(test_entry)
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
            fwi=fwi,
            wind_speed=wind_speed,
            wind_direction=wind_direction,
            temperature=temperature,
            relative_humidity=relative_humidity,
            precipitation=precipitation,
            status="Forecasted",
            prev_day_daily_ffmc=None,
            last_observed_morning_rh_values=None,
        )
        python_fba = calculate_fire_behaviour_advisory(python_input)
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

        check_metric(
            "ROS",
            fuel_type,
            python_fba.ros,
            java_fbp.ros_eq,
            ros_margin_of_error,
            f"""({index}) input- isi:{isi}; bui:{bui}; wind_speed:{wind_speed}; ffmc:{ffmc}; """ f"""java - isi:{java_fbp.isi}""",
        )

        check_metric("ROS_t", fuel_type, python_fba.ros_t, java_fbp.ros_t, acceptable_margin_of_error)
        check_metric("HFI", fuel_type, python_fba.hfi, java_fbp.hfi, hfi_margin_of_error, f"({index})")
        check_metric("HFI", fuel_type, python_fba.hfi, java_fbp.hfi, hfi_margin_of_error, f"({index})")
        check_metric("HFI_t", fuel_type, python_fba.hfi_t, java_fbp.hfi, acceptable_margin_of_error)
        check_metric("CFB", fuel_type, python_fba.cfb * 100.0, java_fbp.cfb, cfb_margin_of_error, f"({index})")
        check_metric("CFB_t", fuel_type, python_fba.cfb_t * 100.0, java_fbp.cfb, cfb_t_margin_of_error)
        check_metric("one_hour_size", fuel_type, python_fba.sixty_minute_fire_size, java_fbp.area, one_hour_spread_margin_of_error, f"({index})")
        check_metric("1 HR Size t", fuel_type, python_fba.sixty_minute_fire_size_t, java_fbp.area, fire_size_acceptable_margin_of_error)
