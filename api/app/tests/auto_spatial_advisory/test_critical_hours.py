import os
import pytest
import json
from app.auto_spatial_advisory.critical_hours import check_station_valid
from app.wildfire_one.schema_parsers import WFWXWeatherStation

dirname = os.path.dirname(__file__)
dailies_fixture = os.path.join(dirname, "wf1-dailies.json")
hourlies_fixture = os.path.join(dirname, "wf1-hourlies.json")
mock_station = WFWXWeatherStation(wfwx_id="bb7cb089-286a-4734-e053-1d09228eeca8", code=169, name="UPPER FULTON", latitude=55.03395, longitude=-126.799667, elevation=900, zone_code=45)


def test_check_station_valid():
    with open(dailies_fixture, "r") as dailies:
        raw_dailies = json.load(dailies)["_embedded"]["dailies"]
        dailies_by_station_id = {raw_dailies[0]["stationId"]: raw_dailies[0]}
        hourlies_by_station_code = {raw_dailies[0]["stationData"]["stationCode"]: []}
        assert check_station_valid(mock_station, dailies_by_station_id, hourlies_by_station_code) == True


@pytest.mark.parametrize(
    "index_key",
    ["duffMoistureCode", "droughtCode", "fineFuelMoistureCode"],
)
def test_check_station_invalid_missing_indices(index_key):
    """
    When a daily is missing DMC, DC or FFMC it is invalid

    :param index_key: DMC, DC or FFMC key for WF1 daily
    """
    with open(dailies_fixture, "r") as dailies:
        raw_dailies = json.load(dailies)["_embedded"]["dailies"]
        daily = raw_dailies[0]
        daily[index_key] = None
        dailies_by_station_id = {raw_dailies[0]["stationId"]: daily}
        hourlies_by_station_code = {raw_dailies[0]["stationData"]["stationCode"]: []}
        assert check_station_valid(mock_station, dailies_by_station_id, hourlies_by_station_code) == False


def test_check_station_invalid_missing_daily():
    """
    When a station daily is missing for a station it is invalid
    """
    with open(dailies_fixture, "r") as dailies:
        raw_dailies = json.load(dailies)["_embedded"]["dailies"]
        dailies_by_station_id = {"1": raw_dailies[0]}
        hourlies_by_station_code = {raw_dailies[0]["stationData"]["stationCode"]: []}
        assert check_station_valid(mock_station, dailies_by_station_id, hourlies_by_station_code) == False


def test_check_station_invalid_missing_hourly():
    """
    When a station hourly is missing for a station it is invalid
    """
    with open(dailies_fixture, "r") as dailies:
        raw_dailies = json.load(dailies)["_embedded"]["dailies"]
        dailies_by_station_id = {raw_dailies[0]["stationId"]: raw_dailies[0]}
        hourlies_by_station_code = {"1": []}
        assert check_station_valid(mock_station, dailies_by_station_id, hourlies_by_station_code) == False
