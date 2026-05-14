import os
import pytest
import math
import numpy as np
import json

from app.auto_spatial_advisory.critical_hours import CriticalHoursInputs, calculate_representative_hours, check_station_valid, determine_start_time, determine_end_time
from wps_shared.schemas.fba_calc import CriticalHoursHFI
from wps_shared.schemas.stations import WFWXWeatherStation


dirname = os.path.dirname(__file__)
dailies_fixture = os.path.join(dirname, "wf1-dailies.json")
hourlies_fixture = os.path.join(dirname, "wf1-hourlies.json")
mock_station = WFWXWeatherStation(wfwx_id="bb7cb089-286a-4734-e053-1d09228eeca8", code=169, name="UPPER FULTON", latitude=55.03395, longitude=-126.799667, elevation=900, zone_code="45")


def test_check_station_valid():
    with open(dailies_fixture, "r") as dailies, open(hourlies_fixture, "r") as hourlies:
        raw_dailies = json.load(dailies)["_embedded"]["dailies"]
        dailies_by_station_id = {raw_dailies[0]["stationId"]: raw_dailies[0]}
        hourlies_by_station_code = json.load(hourlies)
        assert (
            check_station_valid(
                mock_station,
                critical_hours_inputs=CriticalHoursInputs(
                    dailies_by_station_id=dailies_by_station_id, yesterday_dailies_by_station_id={}, hourly_observations_by_station_code=hourlies_by_station_code
                ),
            )
            == True
        )


@pytest.mark.parametrize(
    "index_key",
    ["duffMoistureCode", "droughtCode", "fineFuelMoistureCode"],
)
def test_check_station_invalid_missing_indices(index_key):
    """
    When a daily is missing DMC, DC or FFMC it is invalid

    :param index_key: DMC, DC or FFMC key for WF1 daily
    """
    with open(dailies_fixture, "r") as dailies, open(hourlies_fixture, "r") as hourlies:
        raw_dailies = json.load(dailies)["_embedded"]["dailies"]
        daily = raw_dailies[0]
        daily[index_key] = None
        dailies_by_station_id = {raw_dailies[0]["stationId"]: daily}
        hourlies_by_station_code = json.load(hourlies)
        assert (
            check_station_valid(
                mock_station,
                critical_hours_inputs=CriticalHoursInputs(
                    dailies_by_station_id=dailies_by_station_id, yesterday_dailies_by_station_id={}, hourly_observations_by_station_code=hourlies_by_station_code
                ),
            )
            == False
        )


def test_check_station_invalid_missing_daily():
    """
    When a station daily is missing for a station it is invalid
    """
    with open(hourlies_fixture, "r") as hourlies:
        dailies_by_station_id = {}
        hourlies_by_station_code = json.load(hourlies)
        assert (
            check_station_valid(
                mock_station,
                critical_hours_inputs=CriticalHoursInputs(
                    dailies_by_station_id=dailies_by_station_id, yesterday_dailies_by_station_id={}, hourly_observations_by_station_code=hourlies_by_station_code
                ),
            )
            == False
        )


def test_check_station_invalid_missing_hourly():
    """
    When a station hourly is missing for a station it is invalid
    """
    with open(dailies_fixture, "r") as dailies:
        raw_dailies = json.load(dailies)["_embedded"]["dailies"]
        dailies_by_station_id = {raw_dailies[0]["stationId"]: raw_dailies[0]}
        hourlies_by_station_code = {}
        assert (
            check_station_valid(
                mock_station,
                critical_hours_inputs=CriticalHoursInputs(
                    dailies_by_station_id=dailies_by_station_id, yesterday_dailies_by_station_id={}, hourly_observations_by_station_code=hourlies_by_station_code
                ),
            )
            == False
        )


@pytest.mark.parametrize(
    "start_times, expected_start_time",
    [
        ([1, 2], 1),
        ([1, 2, 3], math.floor(np.percentile([1, 2, 3], 25))),
    ],
)
def test_determine_start_time(start_times, expected_start_time):
    """
    Given a list of start times, choose the minimum if less than 3, otherwise the 25th percentile
    """
    assert determine_start_time(start_times) == expected_start_time


@pytest.mark.parametrize(
    "start_times, expected_start_time",
    [
        ([1, 2], 2),
        ([1, 2, 3], math.ceil(np.percentile([1, 2, 3], 75))),
    ],
)
def test_determine_end_time(start_times, expected_start_time):
    """
    Given a list of end times, choose them maximum if less than 3, otherwise the 75th percentile
    """
    assert determine_end_time(start_times) == expected_start_time


@pytest.mark.parametrize(
    "critical_hours, expected_start_end",
    [
        ([CriticalHoursHFI(start=1, end=2), CriticalHoursHFI(start=1, end=2)], (1, 2)),
        ([CriticalHoursHFI(start=1, end=2), CriticalHoursHFI(start=2, end=14)], (1, 14)),
        (
            [CriticalHoursHFI(start=1, end=1), CriticalHoursHFI(start=2, end=2), CriticalHoursHFI(start=1, end=3)],
            (math.floor(np.percentile([1, 2, 1], 25)), math.ceil(np.percentile([1, 2, 3], 75))),
        ),
    ],
)
def test_representative_hours(critical_hours, expected_start_end):
    """
    Given a list of critical hours, return the representative critical hours
    """
    assert calculate_representative_hours(critical_hours) == expected_start_end
