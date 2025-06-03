from datetime import date
import pytest
from wps_shared.db.models.auto_spatial_advisory import AdvisoryHFIWindSpeed, HfiClassificationThreshold, SFMSFuelType
from wps_shared.schemas.fba import AdvisoryMinWindStats, HfiThreshold

from app.auto_spatial_advisory.zone_stats import get_fuel_type_area_stats, get_optional_percent_curing, get_zone_wind_stats_for_source_id

grass_fuel_type = SFMSFuelType(id=12, fuel_type_id=12, fuel_type_code="O-1a/O-1b", description="Matted or Standing Grass")
non_grass_fuel_type = SFMSFuelType(id=14, fuel_type_id=14, fuel_type_code="M-1/M-2", description="Boreal Mixedwood - Leafless or Green")
advisory_threshold = HfiThreshold(id=1, name="advisory", description="4000 < hfi < 10000")
warning_threshold = HfiThreshold(id=2, name="warning", description="hfi >= 10000")
hfi_threshold_by_id = {1: advisory_threshold, 2: warning_threshold}



def test_percent_curing_non_fuel():
    assert get_optional_percent_curing(date(2024, 10, 31), non_grass_fuel_type) is None


@pytest.mark.parametrize(
    "for_date",
    [
        (date(2024, 11, 1)), # nov 1, start of range
        (date(2024, 12, 22)), # dev 22, mid range
        (date(2024, 7, 15)), # jul 15, end of range
    ],
)
def test_60_percent_curing(for_date: date):
    assert get_optional_percent_curing(for_date, grass_fuel_type) == 60

@pytest.mark.parametrize(
    "for_date",
    [
        (date(2024, 7, 16)), # jul 16, start of range
        (date(2024, 7, 21)), # jul 21, mid range
        (date(2024, 7, 30)), # jul 30, end of range
    ],
)
def test_70_percent_curing(for_date: date):
    assert get_optional_percent_curing(for_date, grass_fuel_type) == 70


@pytest.mark.parametrize(
    "for_date",
    [
        (date(2024, 7, 31)), # jul 31, start of range
        (date(2024, 8, 7)), # aug 7, mid range
        (date(2024, 8, 15)), # aug 15, end of range
    ],
)
def test_80_percent_curing(for_date: date):
    assert get_optional_percent_curing(for_date, grass_fuel_type) == 80


@pytest.mark.parametrize(
    "for_date",
    [
        (date(2024, 8, 16)), # aug 16, start of range
        (date(2024, 9, 15)), # sep 15, mid range
        (date(2024, 10, 31)), # oct 31, end of range
    ],
)
def test_90_percent_curing(for_date: date):
    assert get_optional_percent_curing(for_date, grass_fuel_type) == 90



def test_get_fuel_type_area_stats():
    area=50000
    fuel_area=60000
    res = get_fuel_type_area_stats(date(2024, 11, 1), [(grass_fuel_type, non_grass_fuel_type)], HfiThreshold(id=1, description="4000 < hfi < 10000", name="advisory"), None, critical_hour_start=8, critical_hour_end=12, fuel_type_id=12, area=area, fuel_area=fuel_area)
    assert res.area == area
    assert res.fuel_area == fuel_area
    assert res.percent_curing == 60


def test_get_fuel_type_area_stats_non_grass():
    area=50000
    fuel_area=60000
    res = get_fuel_type_area_stats(date(2024, 11, 1), [(non_grass_fuel_type, grass_fuel_type)], HfiThreshold(id=1, description="4000 < hfi < 10000", name="advisory"), None, critical_hour_start=8, critical_hour_end=12, fuel_type_id=14, area=area, fuel_area=fuel_area)
    assert res.area == area
    assert res.fuel_area == fuel_area
    assert res.percent_curing is None


def test_get_fuel_type_area_stats_percent_conifer():
    area=50000
    fuel_area=60000
    percent_conifer = 1
    res = get_fuel_type_area_stats(date(2024, 11, 1), [(non_grass_fuel_type, grass_fuel_type)], HfiThreshold(id=1, description="4000 < hfi < 10000", name="advisory"), percent_conifer, critical_hour_start=8, critical_hour_end=12, fuel_type_id=14, area=area, fuel_area=fuel_area)
    assert res.area == area
    assert res.fuel_area == fuel_area
    assert res.percent_curing is None
    assert res.fuel_type.fuel_type_code == f"M-1/M-2 (≥{percent_conifer} PC)"



@pytest.mark.parametrize(
    "zone_wind_stats, hfi_thresholds_by_id, expected_advisory_wind_stats",
    [
        ([AdvisoryHFIWindSpeed(id=1, advisory_shape_id=1, threshold=1, run_parameters=1, min_wind_speed=1), AdvisoryHFIWindSpeed(id=2, advisory_shape_id=2, threshold=2, run_parameters=1, min_wind_speed=2)], hfi_threshold_by_id, [AdvisoryMinWindStats(threshold=advisory_threshold, min_wind_speed=1), AdvisoryMinWindStats(threshold=warning_threshold, min_wind_speed=2)]),
        ([], hfi_threshold_by_id, [])
    ],
)
def test_get_zone_wind_stats(zone_wind_stats, hfi_thresholds_by_id, expected_advisory_wind_stats):    
    assert get_zone_wind_stats_for_source_id(zone_wind_stats=zone_wind_stats, hfi_thresholds_by_id=hfi_thresholds_by_id) == expected_advisory_wind_stats
