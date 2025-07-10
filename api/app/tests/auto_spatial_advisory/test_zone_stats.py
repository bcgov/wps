from datetime import date

import pytest

from app.auto_spatial_advisory.zone_stats import (
    get_fuel_type_area_stats,
    get_optional_percent_curing,
    get_zone_wind_stats_for_source_id,
)
from wps_shared.db.models.auto_spatial_advisory import (
    AdvisoryHFIWindSpeed,
    SFMSFuelType,
)
from wps_shared.schemas.fba import AdvisoryMinWindStats, HfiThreshold
from unittest.mock import patch
from app.auto_spatial_advisory.zone_stats import build_zone_stats
from wps_shared.db.models.auto_spatial_advisory import SFMSFuelType as DBSFMSFuelType
from wps_shared.schemas.fba import (
    FireZoneHFIStats,
    SFMSFuelType as SchemaSFMSFuelType,
)

grass_fuel_type = SFMSFuelType(
    id=12, fuel_type_id=12, fuel_type_code="O-1a/O-1b", description="Matted or Standing Grass"
)
non_grass_fuel_type = SFMSFuelType(
    id=14,
    fuel_type_id=14,
    fuel_type_code="M-1/M-2",
    description="Boreal Mixedwood - Leafless or Green",
)
advisory_threshold = HfiThreshold(id=1, name="advisory", description="4000 < hfi < 10000")
warning_threshold = HfiThreshold(id=2, name="warning", description="hfi >= 10000")
hfi_threshold_by_id = {1: advisory_threshold, 2: warning_threshold}


def test_percent_curing_non_fuel():
    assert get_optional_percent_curing(date(2024, 10, 31), non_grass_fuel_type) is None


@pytest.mark.parametrize(
    "for_date",
    [
        (date(2024, 11, 1)),  # nov 1, start of range
        (date(2024, 12, 22)),  # dev 22, mid range
        (date(2024, 7, 15)),  # jul 15, end of range
    ],
)
def test_60_percent_curing(for_date: date):
    assert get_optional_percent_curing(for_date, grass_fuel_type) == 60


@pytest.mark.parametrize(
    "for_date",
    [
        (date(2024, 7, 16)),  # jul 16, start of range
        (date(2024, 7, 21)),  # jul 21, mid range
        (date(2024, 7, 30)),  # jul 30, end of range
    ],
)
def test_70_percent_curing(for_date: date):
    assert get_optional_percent_curing(for_date, grass_fuel_type) == 70


@pytest.mark.parametrize(
    "for_date",
    [
        (date(2024, 7, 31)),  # jul 31, start of range
        (date(2024, 8, 7)),  # aug 7, mid range
        (date(2024, 8, 15)),  # aug 15, end of range
    ],
)
def test_80_percent_curing(for_date: date):
    assert get_optional_percent_curing(for_date, grass_fuel_type) == 80


@pytest.mark.parametrize(
    "for_date",
    [
        (date(2024, 8, 16)),  # aug 16, start of range
        (date(2024, 9, 15)),  # sep 15, mid range
        (date(2024, 10, 31)),  # oct 31, end of range
    ],
)
def test_90_percent_curing(for_date: date):
    assert get_optional_percent_curing(for_date, grass_fuel_type) == 90


def test_get_fuel_type_area_stats():
    area = 50000
    fuel_area = 60000
    res = get_fuel_type_area_stats(
        date(2024, 11, 1),
        [grass_fuel_type, non_grass_fuel_type],
        HfiThreshold(id=1, description="4000 < hfi < 10000", name="advisory"),
        None,
        critical_hour_start=8,
        critical_hour_end=12,
        fuel_type_id=12,
        area=area,
        fuel_area=fuel_area,
    )
    assert res.area == area
    assert res.fuel_area == fuel_area
    assert res.percent_curing == 60


def test_get_fuel_type_area_stats_non_grass():
    area = 50000
    fuel_area = 60000
    res = get_fuel_type_area_stats(
        date(2024, 11, 1),
        [non_grass_fuel_type, grass_fuel_type],
        HfiThreshold(id=1, description="4000 < hfi < 10000", name="advisory"),
        None,
        critical_hour_start=8,
        critical_hour_end=12,
        fuel_type_id=14,
        area=area,
        fuel_area=fuel_area,
    )
    assert res.area == area
    assert res.fuel_area == fuel_area
    assert res.percent_curing is None


def test_get_fuel_type_area_stats_percent_conifer():
    area = 50000
    fuel_area = 60000
    percent_conifer = 1
    res = get_fuel_type_area_stats(
        date(2024, 11, 1),
        [non_grass_fuel_type, grass_fuel_type],
        HfiThreshold(id=1, description="4000 < hfi < 10000", name="advisory"),
        percent_conifer,
        critical_hour_start=8,
        critical_hour_end=12,
        fuel_type_id=14,
        area=area,
        fuel_area=fuel_area,
    )
    assert res.area == area
    assert res.fuel_area == fuel_area
    assert res.percent_curing is None
    assert res.fuel_type.fuel_type_code == f"M-1/M-2 (≥{percent_conifer} PC)"


@pytest.mark.parametrize(
    "zone_wind_stats, hfi_thresholds_by_id, expected_advisory_wind_stats",
    [
        (
            [
                AdvisoryHFIWindSpeed(
                    id=1, advisory_shape_id=1, threshold=1, run_parameters=1, min_wind_speed=1
                ),
                AdvisoryHFIWindSpeed(
                    id=2, advisory_shape_id=2, threshold=2, run_parameters=1, min_wind_speed=2
                ),
            ],
            hfi_threshold_by_id,
            [
                AdvisoryMinWindStats(threshold=advisory_threshold, min_wind_speed=1),
                AdvisoryMinWindStats(threshold=warning_threshold, min_wind_speed=2),
            ],
        ),
        ([], hfi_threshold_by_id, []),
    ],
)
def test_get_zone_wind_stats(zone_wind_stats, hfi_thresholds_by_id, expected_advisory_wind_stats):
    assert (
        get_zone_wind_stats_for_source_id(
            zone_wind_stats=zone_wind_stats, hfi_thresholds_by_id=hfi_thresholds_by_id
        )
        == expected_advisory_wind_stats
    )


def make_db_fuel_type(id, fuel_type_id, fuel_type_code, description):
    return DBSFMSFuelType(
        id=id,
        fuel_type_id=fuel_type_id,
        fuel_type_code=fuel_type_code,
        description=description,
    )


def make_schema_fuel_type(fuel_type_id, fuel_type_code, description):
    return SchemaSFMSFuelType(
        fuel_type_id=fuel_type_id,
        fuel_type_code=fuel_type_code,
        description=description,
    )


def test_build_zone_stats_basic():
    zone_source_ids = ["1"]
    hfi_fuel_type_ids_by_zone = {
        "1": [
            # critical_hour_start, critical_hour_end, fuel_type_id, threshold_id, area, fuel_area, percent_conifer
            (8, 12, 12, 1, 1000.0, 1200.0, None),
        ]
    }
    hfi_thresholds_by_id = {
        1: HfiThreshold(id=1, name="advisory", description="4000 < hfi < 10000"),
    }
    fuel_types = [
        make_db_fuel_type(12, 12, "O-1a/O-1b", "Matted or Standing Grass"),
    ]
    for_date = date(2024, 11, 1)
    zone_wind_stats_by_source_id = {
        1: [
            AdvisoryMinWindStats(
                threshold=hfi_thresholds_by_id[1],
                min_wind_speed=5.0,
            )
        ]
    }

    result = build_zone_stats(
        zone_source_ids,
        hfi_fuel_type_ids_by_zone,
        hfi_thresholds_by_id,
        fuel_types,
        for_date,
        zone_wind_stats_by_source_id,
    )

    assert 1 in result
    zone_stats = result[1]
    assert isinstance(zone_stats, FireZoneHFIStats)
    assert zone_stats.min_wind_stats == zone_wind_stats_by_source_id[1]
    assert len(zone_stats.fuel_area_stats) == 1
    fuel_stat = zone_stats.fuel_area_stats[0]
    assert fuel_stat.fuel_type.fuel_type_id == 12
    assert fuel_stat.threshold == hfi_thresholds_by_id[1]
    assert fuel_stat.area == 1000.0
    assert fuel_stat.fuel_area == 1200.0
    assert fuel_stat.percent_curing == 60


def test_build_zone_stats_multiple_zones_and_thresholds():
    zone_source_ids = ["1", "2"]
    hfi_thresholds_by_id = {
        1: HfiThreshold(id=1, name="advisory", description="4000 < hfi < 10000"),
        2: HfiThreshold(id=2, name="warning", description="hfi >= 10000"),
    }
    fuel_types = [
        make_db_fuel_type(12, 12, "O-1a/O-1b", "Matted or Standing Grass"),
        make_db_fuel_type(14, 14, "M-1/M-2", "Boreal Mixedwood"),
    ]
    hfi_fuel_type_ids_by_zone = {
        "1": [
            (8, 12, 12, 1, 1000.0, 1200.0, None),
            (9, 13, 14, 2, 2000.0, 2200.0, 5),
        ],
        "2": [
            (10, 14, 14, 2, 3000.0, 3200.0, None),
        ],
    }
    for_date = date(2024, 8, 20)
    zone_wind_stats_by_source_id = {
        1: [
            AdvisoryMinWindStats(
                threshold=hfi_thresholds_by_id[1],
                min_wind_speed=4.0,
            )
        ],
        2: [
            AdvisoryMinWindStats(
                threshold=hfi_thresholds_by_id[2],
                min_wind_speed=7.0,
            )
        ],
    }

    result = build_zone_stats(
        zone_source_ids,
        hfi_fuel_type_ids_by_zone,
        hfi_thresholds_by_id,
        fuel_types,
        for_date,
        zone_wind_stats_by_source_id,
    )

    assert set(result.keys()) == {1, 2}
    # Zone 1
    z1 = result[1]
    assert len(z1.fuel_area_stats) == 2
    assert z1.fuel_area_stats[0].fuel_type.fuel_type_id == 12
    assert z1.fuel_area_stats[0].percent_curing == 90  # for_date in Aug 20
    assert z1.fuel_area_stats[1].fuel_type.fuel_type_id == 14
    assert z1.fuel_area_stats[1].fuel_type.fuel_type_code == "M-1/M-2 (≥5 PC)"
    # Zone 2
    z2 = result[2]
    assert len(z2.fuel_area_stats) == 1
    assert z2.fuel_area_stats[0].fuel_type.fuel_type_id == 14
    assert z2.fuel_area_stats[0].percent_curing is None


def test_build_zone_stats_missing_threshold_logs_error(caplog):
    zone_source_ids = ["1"]
    hfi_fuel_type_ids_by_zone = {
        "1": [
            (8, 12, 12, 99, 1000.0, 1200.0, None),  # 99 does not exist in thresholds
        ]
    }
    hfi_thresholds_by_id = {
        1: HfiThreshold(id=1, name="advisory", description="4000 < hfi < 10000"),
    }
    fuel_types = [
        make_db_fuel_type(12, 12, "O-1a/O-1b", "Matted or Standing Grass"),
    ]
    for_date = date(2024, 11, 1)
    zone_wind_stats_by_source_id = {}

    with caplog.at_level("ERROR"):
        result = build_zone_stats(
            zone_source_ids,
            hfi_fuel_type_ids_by_zone,
            hfi_thresholds_by_id,
            fuel_types,
            for_date,
            zone_wind_stats_by_source_id,
        )
        assert "No hfi threshold for id: 99" in caplog.text
        assert result[1].fuel_area_stats == []


def test_build_zone_stats_empty_zone():
    zone_source_ids = ["1"]
    hfi_fuel_type_ids_by_zone = {}
    hfi_thresholds_by_id = {}
    fuel_types = []
    for_date = date(2024, 11, 1)
    zone_wind_stats_by_source_id = {}

    result = build_zone_stats(
        zone_source_ids,
        hfi_fuel_type_ids_by_zone,
        hfi_thresholds_by_id,
        fuel_types,
        for_date,
        zone_wind_stats_by_source_id,
    )
    assert 1 in result
    assert result[1].fuel_area_stats == []
    assert result[1].min_wind_stats == []
