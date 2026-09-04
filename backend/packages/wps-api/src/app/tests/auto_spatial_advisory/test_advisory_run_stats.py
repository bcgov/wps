"""Unit tests for app.auto_spatial_advisory.advisory_run_stats.stats: get_all_zone_data_for_source_ids,
and the cache-aware public functions (get_provincial_summary, get_hfi_stats, get_tpi_stats, and
their fire-centre-scoped counterparts)."""

import asyncio
from collections import namedtuple
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from wps_shared.db.models.auto_spatial_advisory import (
    AdvisoryHFIWindSpeed,
    SFMSFuelType,
    TPIClassEnum,
)
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.schemas.fba import (
    FireCentreTPIResponse,
    HFIStatsResponse,
    HfiThreshold,
    ProvincialSummaryResponse,
    TPIResponse,
)

from app.auto_spatial_advisory.advisory_run_stats import (
    get_all_zone_data_for_source_ids,
    get_fire_centre_hfi_stats,
    get_fire_centre_tpi_stats,
    get_hfi_stats,
    get_provincial_summary,
    get_tpi_stats,
)
from app.auto_spatial_advisory.process_hfi import RunType

FIRE_CENTRE_NAME = "Kamloops Fire Centre"

FOR_DATE = date(2024, 7, 15)
RUN_DATETIME = datetime(2024, 7, 15, 12, tzinfo=timezone.utc)
ZONE_SOURCE_ID = "1"

mock_fuel_type_raster = FuelTypeRaster(
    id=1,
    year=2024,
    version=1,
    xsize=100,
    ysize=200,
    object_store_path="test/path",
    content_hash="abc123",
    create_timestamp=datetime(2024, 5, 1, tzinfo=timezone.utc),
)

mock_prev_fuel_type_raster = FuelTypeRaster(
    id=2,
    year=2023,
    version=1,
    xsize=100,
    ysize=200,
    object_store_path="test/path/prev",
    content_hash="def456",
    create_timestamp=datetime(2023, 5, 1, tzinfo=timezone.utc),
)

mock_hfi_thresholds = {1: HfiThreshold(id=1, description="4000 < hfi < 10000", name="advisory")}

mock_fuel_types = [
    SFMSFuelType(id=1, fuel_type_id=1, fuel_type_code="C2", description="test fuel type c2")
]

# (critical_hour_start, critical_hour_end, fuel_type_id, threshold_id, area, fuel_area, percent_conifer)
SAMPLE_ROW = (9.0, 11.0, 1, 1, 50, 100, 1)


def make_session():
    return MagicMock()


def patch_common_deps(mocker):
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_sfms_fuel_type_records",
        return_value=mock_fuel_types,
    )
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_hfi_thresholds_by_id",
        return_value=mock_hfi_thresholds,
    )
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_min_wind_speed_hfi_thresholds",
        return_value={},
    )
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_fuel_type_raster_by_year",
        return_value=mock_fuel_type_raster,
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "precomputed_rows",
    [
        pytest.param([SAMPLE_ROW], id="single_row"),
        pytest.param([SAMPLE_ROW, SAMPLE_ROW, SAMPLE_ROW], id="duplicate_rows"),
    ],
)
async def test_precomputed_rows_deduplicated_to_one_fuel_stat(mocker, precomputed_rows):
    """Duplicate rows from get_precomputed_stats_for_shape are deduplicated to one fuel_area_stats entry."""
    patch_common_deps(mocker)
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_precomputed_stats_for_shape",
        return_value=precomputed_rows,
    )

    result = await get_all_zone_data_for_source_ids(
        make_session(), [ZONE_SOURCE_ID], RunType.FORECAST, FOR_DATE, RUN_DATETIME
    )

    assert 1 in result
    assert len(result[1].fuel_area_stats) == 1


@pytest.mark.anyio
@pytest.mark.parametrize(
    "first_precomputed_result",
    [
        pytest.param([], id="empty_list"),
        pytest.param(None, id="none_result"),
    ],
)
async def test_falls_back_to_prev_year_raster(mocker, first_precomputed_result):
    """Falls back to previous year's fuel raster when current year returns empty or None."""
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_sfms_fuel_type_records",
        return_value=mock_fuel_types,
    )
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_hfi_thresholds_by_id",
        return_value=mock_hfi_thresholds,
    )
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_min_wind_speed_hfi_thresholds",
        return_value={},
    )
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_fuel_type_raster_by_year",
        side_effect=[mock_fuel_type_raster, mock_prev_fuel_type_raster],
    )
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_precomputed_stats_for_shape",
        side_effect=[first_precomputed_result, [SAMPLE_ROW]],
    )

    result = await get_all_zone_data_for_source_ids(
        make_session(), [ZONE_SOURCE_ID], RunType.FORECAST, FOR_DATE, RUN_DATETIME
    )

    assert 1 in result
    assert len(result[1].fuel_area_stats) == 1


@pytest.mark.anyio
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_sfms_fuel_type_records",
    new_callable=AsyncMock,
    return_value=mock_fuel_types,
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_hfi_thresholds_by_id",
    new_callable=AsyncMock,
    return_value=mock_hfi_thresholds,
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_min_wind_speed_hfi_thresholds",
    new_callable=AsyncMock,
    return_value={},
)
async def test_no_data_for_either_year_returns_empty_fuel_stats(*_):
    """Returns an empty fuel_area_stats list when neither year has precomputed stats."""
    with patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_fuel_type_raster_by_year",
        new_callable=AsyncMock,
        side_effect=[mock_fuel_type_raster, mock_prev_fuel_type_raster],
    ):
        with patch(
            "app.auto_spatial_advisory.advisory_run_stats.stats.get_precomputed_stats_for_shape",
            new_callable=AsyncMock,
            side_effect=[[], []],
        ):
            result = await get_all_zone_data_for_source_ids(
                make_session(), [ZONE_SOURCE_ID], RunType.FORECAST, FOR_DATE, RUN_DATETIME
            )

    assert 1 in result
    assert result[1].fuel_area_stats == []


@pytest.mark.anyio
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_sfms_fuel_type_records",
    new_callable=AsyncMock,
    return_value=mock_fuel_types,
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_fuel_type_raster_by_year",
    new_callable=AsyncMock,
    return_value=mock_fuel_type_raster,
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_hfi_thresholds_by_id",
    new_callable=AsyncMock,
    return_value={},
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_min_wind_speed_hfi_thresholds",
    new_callable=AsyncMock,
    return_value={},
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_precomputed_stats_for_shape",
    new_callable=AsyncMock,
    return_value=[SAMPLE_ROW],
)
async def test_missing_threshold_skips_row(*_):
    """Skips rows whose threshold_id is not in hfi_thresholds_by_id."""
    result = await get_all_zone_data_for_source_ids(
        make_session(), [ZONE_SOURCE_ID], RunType.FORECAST, FOR_DATE, RUN_DATETIME
    )
    assert 1 in result
    assert result[1].fuel_area_stats == []


@pytest.mark.anyio
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_sfms_fuel_type_records",
    new_callable=AsyncMock,
    return_value=mock_fuel_types,
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_fuel_type_raster_by_year",
    new_callable=AsyncMock,
    return_value=mock_fuel_type_raster,
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_hfi_thresholds_by_id",
    new_callable=AsyncMock,
    return_value=mock_hfi_thresholds,
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_min_wind_speed_hfi_thresholds",
    new_callable=AsyncMock,
    return_value={
        1: (
            AdvisoryHFIWindSpeed(
                id=1, advisory_shape_id=1, threshold=1, run_parameters=1, min_wind_speed=5.0
            ),
        )
    },
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_precomputed_stats_for_shape",
    new_callable=AsyncMock,
    return_value=[SAMPLE_ROW],
)
async def test_wind_stats_attached_to_correct_zone(*_):
    """Wind stats for a zone source ID are included in the corresponding FireZoneHFIStats."""
    result = await get_all_zone_data_for_source_ids(
        make_session(), [ZONE_SOURCE_ID], RunType.FORECAST, FOR_DATE, RUN_DATETIME
    )
    assert 1 in result
    assert len(result[1].min_wind_stats) == 1
    assert result[1].min_wind_stats[0].min_wind_speed == pytest.approx(5.0)


@pytest.mark.anyio
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_sfms_fuel_type_records",
    new_callable=AsyncMock,
    return_value=mock_fuel_types,
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_fuel_type_raster_by_year",
    new_callable=AsyncMock,
    return_value=mock_fuel_type_raster,
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_hfi_thresholds_by_id",
    new_callable=AsyncMock,
    return_value=mock_hfi_thresholds,
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_min_wind_speed_hfi_thresholds",
    new_callable=AsyncMock,
    return_value={},
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_precomputed_stats_for_shape",
    new_callable=AsyncMock,
    return_value=[SAMPLE_ROW],
)
async def test_zone_without_wind_speed_data_has_empty_min_wind_stats(*_):
    """Zones with no wind speed data in the response get an empty min_wind_stats list."""
    result = await get_all_zone_data_for_source_ids(
        make_session(), [ZONE_SOURCE_ID], RunType.FORECAST, FOR_DATE, RUN_DATETIME
    )
    assert 1 in result
    assert result[1].min_wind_stats == []


@pytest.mark.anyio
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_sfms_fuel_type_records",
    new_callable=AsyncMock,
    return_value=mock_fuel_types,
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_fuel_type_raster_by_year",
    new_callable=AsyncMock,
    return_value=mock_fuel_type_raster,
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_hfi_thresholds_by_id",
    new_callable=AsyncMock,
    return_value=mock_hfi_thresholds,
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_min_wind_speed_hfi_thresholds",
    new_callable=AsyncMock,
    return_value={},
)
@patch(
    "app.auto_spatial_advisory.advisory_run_stats.stats.get_precomputed_stats_for_shape",
    new_callable=AsyncMock,
    return_value=[],
)
async def test_empty_zone_source_ids_returns_empty_dict(mock_precomputed, *_):
    """Returns an empty dict when zone_source_ids is empty."""
    result = await get_all_zone_data_for_source_ids(
        make_session(), [], RunType.FORECAST, FOR_DATE, RUN_DATETIME
    )
    assert result == {}
    mock_precomputed.assert_not_called()


TpiStatsRow = namedtuple(
    "TpiStatsRow",
    ["source_identifier", "pixel_size_metres", "valley_bottom", "mid_slope", "upper_slope"],
)


@pytest.mark.anyio
async def test_get_provincial_summary_cache_hit_skips_db(mocker):
    cached_response = ProvincialSummaryResponse(provincial_summary=[])
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.asa_stats_cache.get_cached_provincial_summary",
        new_callable=AsyncMock,
        return_value=cached_response,
    )
    mock_rollup = mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_provincial_rollup",
        new_callable=AsyncMock,
    )

    result = await get_provincial_summary(RunType.FORECAST, RUN_DATETIME, FOR_DATE)

    assert result is cached_response
    mock_rollup.assert_not_called()


@pytest.mark.anyio
async def test_get_provincial_summary_cache_miss_fetches_and_caches(mocker):
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.asa_stats_cache.get_cached_provincial_summary",
        new_callable=AsyncMock,
        return_value=None,
    )
    mocker.patch("app.auto_spatial_advisory.advisory_run_stats.stats.get_async_read_session_scope")
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_provincial_rollup",
        new_callable=AsyncMock,
        return_value=[],
    )
    mock_put = mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.asa_stats_cache.put_cached_provincial_summary",
        new_callable=AsyncMock,
    )

    result = await get_provincial_summary(RunType.FORECAST, RUN_DATETIME, FOR_DATE)

    assert result == ProvincialSummaryResponse(provincial_summary=[])
    mock_put.assert_called_once()


@pytest.mark.anyio
async def test_get_hfi_stats_cache_hit_skips_db(mocker):
    cached_response = HFIStatsResponse(zone_data={})
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.asa_stats_cache.get_cached_hfi_stats",
        new_callable=AsyncMock,
        return_value=cached_response,
    )
    mock_zone_data = mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_zone_data_for_source_ids",
        new_callable=AsyncMock,
    )

    result = await get_hfi_stats(RunType.FORECAST, RUN_DATETIME, FOR_DATE)

    assert result is cached_response
    mock_zone_data.assert_not_called()


@pytest.mark.anyio
async def test_get_tpi_stats_cache_hit_skips_db(mocker):
    cached_response = TPIResponse(firezone_tpi_stats=[])
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.asa_stats_cache.get_cached_tpi_stats",
        new_callable=AsyncMock,
        return_value=cached_response,
    )
    mock_fetch = mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.fetch_tpi_stats_rows",
        new_callable=AsyncMock,
    )

    result = await get_tpi_stats(RunType.FORECAST, RUN_DATETIME, FOR_DATE)

    assert result is cached_response
    mock_fetch.assert_not_called()


@pytest.mark.anyio
async def test_get_tpi_stats_cache_miss_builds_all_tpi_classes(mocker):
    """Covers all three TPIClassEnum branches (valley_bottom, mid_slope, upper_slope) in one
    zone's stats, and confirms the cache-miss result gets stored."""
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.asa_stats_cache.get_cached_tpi_stats",
        new_callable=AsyncMock,
        return_value=None,
    )
    mocker.patch("app.auto_spatial_advisory.advisory_run_stats.stats.get_async_read_session_scope")
    row = TpiStatsRow(
        source_identifier=1, pixel_size_metres=2, valley_bottom=1, mid_slope=2, upper_slope=3
    )
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.fetch_tpi_stats_rows",
        new_callable=AsyncMock,
        return_value=[row],
    )
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_fuel_type_raster_by_year",
        new_callable=AsyncMock,
        return_value=mock_fuel_type_raster,
    )
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_tpi_fuel_areas",
        new_callable=AsyncMock,
        return_value=[
            (TPIClassEnum.valley_bottom, 10, 1),
            (TPIClassEnum.mid_slope, 20, 1),
            (TPIClassEnum.upper_slope, 30, 1),
            # A 4th entry after upper_slope so the loop continues past that elif branch
            # instead of upper_slope always being the last iteration. This covers
            # "matched upper_slope, then loop continues" branch, not just "matched and exits".
            (TPIClassEnum.valley_bottom, 11, 1),
        ],
    )
    mock_put = mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.asa_stats_cache.put_cached_tpi_stats",
        new_callable=AsyncMock,
    )

    result = await get_tpi_stats(RunType.FORECAST, RUN_DATETIME, FOR_DATE)

    zone_stats = result.firezone_tpi_stats[0]
    assert zone_stats.valley_bottom_tpi == 11  # overwritten by the later duplicate entry
    assert zone_stats.mid_slope_tpi == 20
    assert zone_stats.upper_slope_tpi == 30
    mock_put.assert_called_once()


@pytest.mark.anyio
async def test_get_fire_centre_hfi_stats_cache_hit_skips_db(mocker):
    cached_response = {}
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.asa_stats_cache.get_cached_fire_centre_hfi_stats",
        new_callable=AsyncMock,
        return_value=cached_response,
    )
    mock_zone_data = mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_all_zone_data_for_source_ids",
        new_callable=AsyncMock,
    )

    result = await get_fire_centre_hfi_stats(
        FIRE_CENTRE_NAME, RunType.FORECAST, RUN_DATETIME, FOR_DATE
    )

    assert result is cached_response
    mock_zone_data.assert_not_called()


@pytest.mark.anyio
async def test_get_fire_centre_tpi_stats_cache_hit_skips_db(mocker):
    cached_response = FireCentreTPIResponse(
        fire_centre_name=FIRE_CENTRE_NAME, firezone_tpi_stats=[]
    )
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.asa_stats_cache.get_cached_fire_centre_tpi_stats",
        new_callable=AsyncMock,
        return_value=cached_response,
    )
    mock_centre_tpi_stats = mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_centre_tpi_stats",
        new_callable=AsyncMock,
    )

    result = await get_fire_centre_tpi_stats(
        FIRE_CENTRE_NAME, RunType.FORECAST, RUN_DATETIME, FOR_DATE
    )

    assert result is cached_response
    mock_centre_tpi_stats.assert_not_called()


@pytest.mark.anyio
async def test_get_provincial_summary_concurrent_callers_compute_once(mocker):
    """A burst of concurrent callers for the same (run_type, run_datetime, for_date) must not
    each recompute independently -- that's the cache-stampede this locking exists to prevent.
    Only the first caller should reach get_provincial_rollup; everyone else should block on the
    lock and then read back what the first caller cached."""
    stored: dict = {}

    async def fake_get_cached(*_args):
        return stored.get("value")

    async def fake_put_cached(*args):
        stored["value"] = args[-1]

    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.asa_stats_cache.get_cached_provincial_summary",
        side_effect=fake_get_cached,
    )
    mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.asa_stats_cache.put_cached_provincial_summary",
        side_effect=fake_put_cached,
    )
    mocker.patch("app.auto_spatial_advisory.advisory_run_stats.stats.get_async_read_session_scope")

    async def slow_rollup(*_args, **_kwargs):
        # Holds the lock long enough for other concurrent callers to queue up behind it.
        await asyncio.sleep(0.05)
        return []

    mock_rollup = mocker.patch(
        "app.auto_spatial_advisory.advisory_run_stats.stats.get_provincial_rollup",
        side_effect=slow_rollup,
    )

    concurrent_for_date = date(2099, 1, 1)  # unique key: isolates this test's lock from others
    results = await asyncio.gather(
        *(
            get_provincial_summary(RunType.FORECAST, RUN_DATETIME, concurrent_for_date)
            for _ in range(10)
        )
    )

    assert mock_rollup.call_count == 1
    assert all(result == ProvincialSummaryResponse(provincial_summary=[]) for result in results)
