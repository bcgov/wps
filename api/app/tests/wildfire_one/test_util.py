from typing import Optional
from app.wildfire_one.util import is_station_valid


def build_station(status: str, lat: Optional[int], long: Optional[int]):
    return {
        "latitude": lat,
        "longitude": long,
        "stationStatus": {
            "id": status,
        }
    }


def test_valid_active_station():
    """ Returns stations based on raw wf1 stations """
    station = build_station("ACTIVE", 1, 1)

    result = is_station_valid(station)
    assert result == True


def test_valid_project_station():
    """ Returns stations based on raw wf1 stations """
    station = build_station("PROJECT", 1, 1)

    result = is_station_valid(station)
    assert result == True


def test_valid_test_station():
    """ Returns stations based on raw wf1 stations """
    station = build_station("TEST", 1, 1)

    result = is_station_valid(station)
    assert result == True


def test_invalid_status_station():
    """ Returns stations based on raw wf1 stations """
    station = build_station("", 1, 1)

    result = is_station_valid(station)
    assert result == False


def test_invalid_lat_station():
    """ Returns stations based on raw wf1 stations """
    station = build_station("ACTIVE", None, 1)

    result = is_station_valid(station)
    assert result == False


def test_invalid_long_station():
    """ Returns stations based on raw wf1 stations """
    station = build_station("ACTIVE", 1, None)

    result = is_station_valid(station)
    assert result == False
