import asyncio
import json
import math
from collections import namedtuple
from datetime import date, datetime, timezone
from unittest.mock import patch

import app.main
import pytest
from aiohttp import ClientSession
from app.tests import get_complete_filename
from fastapi.testclient import TestClient

from wps_shared.db.models.auto_spatial_advisory import (
    AdvisoryHFIWindSpeed,
    AdvisoryTPIStats,
    RunParameters,
    SFMSFuelType,
    TPIClassEnum,
)
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.schemas.auto_spatial_advisory import SFMSRunType
from wps_shared.schemas.fba import (
    FireZoneHFIStats,
    HFIStatsResponse,
    HfiThreshold,
    LatestSFMSRunParameterRangeResponse,
    SFMSRunParameter,
)
from wps_shared.tests.common import default_mock_client_get

mock_fire_centre_name = "PGFireCentre"

get_fire_centres_url = "/api/fba/fire-centers"
get_fire_zone_areas_url = "/api/fba/fire-shape-areas/forecast/2022-09-27/2022-09-27"
get_fire_centre_info_url = (
    "/api/fba/fire-centre-hfi-stats/forecast/2022-09-27/2022-09-27/Kamloops%20Fire%20Centre"
)
get_fire_centre_tpi_stats_url = (
    f"/api/fba/fire-centre-tpi-stats/forecast/2024-08-10/2024-08-10/{mock_fire_centre_name}"
)
get_sfms_run_datetimes_url = "/api/fba/sfms-run-datetimes/forecast/2022-09-27"
get_sfms_run_bounds_url = "/api/fba/sfms-run-bounds"
get_tpi_stats_url = "api/fba/tpi-stats/forecast/2022-09-27/2022-09-27"

decode_fn = "jwt.decode"

mock_tpi_stats_empty = []

mock_fire_centre_info = [(9.0, 11.0, 1, 1, 50, 100, 1)]
mock_fire_centre_info_with_grass = [(9.0, 11.0, 12, 1, 50, 100, None)]
mock_fuel_type_raster = FuelTypeRaster(
    id=1,
    year=2024,
    version=2,
    xsize=100,
    ysize=200,
    object_store_path="test/path",
    content_hash="abc123",
    create_timestamp=datetime(2024, 5, 31, 20, tzinfo=timezone.utc),
)

mock_sfms_run_datetimes = [
    RunParameters(
        id=1,
        run_type="forecast",
        run_datetime=datetime(year=2024, month=1, day=1, hour=1, tzinfo=timezone.utc),
        for_date=date(year=2024, month=1, day=2),
    )
]

CentreHFIFuelResponse = namedtuple(
    "CentreHFIFuelResponse",
    [
        "advisory_shape_id",
        "source_identifier",
        "valley_bottom",
        "mid_slope",
        "upper_slope",
        "pixel_size_metres",
    ],
)

def create_mock_centre_tpi_stats(
    advisory_shape_id, source_identifier, valley_bottom, mid_slope, upper_slope, pixel_size_metres
):
    return CentreHFIFuelResponse(
        advisory_shape_id=advisory_shape_id,
        source_identifier=source_identifier,
        valley_bottom=valley_bottom,
        mid_slope=mid_slope,
        upper_slope=upper_slope,
        pixel_size_metres=pixel_size_metres,
    )


mock_centre_tpi_stats_1 = create_mock_centre_tpi_stats(1, 1, 1, 2, 3, 2)
mock_centre_tpi_stats_2 = create_mock_centre_tpi_stats(2, 2, 1, 2, 3, 2)

TPIFuelAreasResponse = namedtuple(
    "TPIFuelAreasResponse",
    [
        "tpi_class",
        "fuel_area",
        "source_identifier",
        "id",
        "name",
    ],
)


def mock_create_tpi_fuel_area(tpi_class, fuel_area, source_identifier, id, name):
    return TPIFuelAreasResponse(
        tpi_class=tpi_class,
        fuel_area=fuel_area,
        source_identifier=source_identifier,
        id=id,
        name=name,
    )


mock_tpi_fuel_area_1 = mock_create_tpi_fuel_area(
    TPIClassEnum.valley_bottom, 100, "20", 2, "Coastal"
)
mock_tpi_fuel_area_2 = mock_create_tpi_fuel_area(TPIClassEnum.mid_slope, 200, "20", 2, "Coastal")
mock_tpi_fuel_area_3 = mock_create_tpi_fuel_area(TPIClassEnum.upper_slope, 300, "20", 2, "Coastal")

TPIStatsResponse = namedtuple(
    "TPIStatsResponse",
    [
        "advisory_shape_id",
        "source_identifier",
        "valley_bottom",
        "mid_slope",
        "upper_slope",
        "pixel_size_metres",
        "fire_centre_id",
        "fire_centre_name",
    ],
)


def create_mock_tpi_stats(
    advisory_shape_id,
    source_identifier,
    valley_bottom,
    mid_slope,
    upper_slope,
    pixel_size_metres,
    fire_centre_id,
    fire_centre_name,
):
    return TPIStatsResponse(
        advisory_shape_id=advisory_shape_id,
        source_identifier=source_identifier,
        valley_bottom=valley_bottom,
        mid_slope=mid_slope,
        upper_slope=upper_slope,
        pixel_size_metres=pixel_size_metres,
        fire_centre_id=fire_centre_id,
        fire_centre_name=fire_centre_name,
    )


mock_tpi_stats_1 = create_mock_tpi_stats(1, 1, 1, 2, 3, 2, 1, "foo")
mock_tpi_stats_2 = create_mock_tpi_stats(2, 2, 1, 2, 3, 2, 2, "bar")


CentreTPIFuelAreasResponse = namedtuple(
    "CentreTPIFuelAreasResponse", ["tpi_class", "fuel_area", "source_identifier"]
)


def create_mock_centre_tpi_fuel_area_response(tpi_class, fuel_area, source_identifier):
    return CentreTPIFuelAreasResponse(
        tpi_class=tpi_class, fuel_area=fuel_area, source_identifier=source_identifier
    )


mock_centre_tpi_fuel_area_1 = create_mock_centre_tpi_fuel_area_response(
    TPIClassEnum.valley_bottom, 1, 1
)
mock_centre_tpi_fuel_area_2 = create_mock_centre_tpi_fuel_area_response(
    TPIClassEnum.mid_slope, 2, 1
)
mock_centre_tpi_fuel_area_3 = create_mock_centre_tpi_fuel_area_response(
    TPIClassEnum.upper_slope, 3, 1
)


async def mock_get_fire_centres(*_, **__):
    return []


async def mock_get_hfi_area(*_, **__):
    return []


async def mock_get_auth_header(*_, **__):
    return {}


async def mock_get_tpi_stats_empty(*_, **__):
    await asyncio.sleep(0)
    return mock_tpi_stats_empty


async def mock_get_tpi_stats_none(*_, **__):
    return None


async def mock_get_fire_centre_info(*_, **__):
    return mock_fire_centre_info


async def mock_get_fuel_type_raster_by_year(*_):
    return mock_fuel_type_raster


async def mock_get_fire_centre_info_with_grass(*_, **__):
    return mock_fire_centre_info_with_grass


async def mock_get_centre_tpi_stats(*_, **__):
    return [mock_centre_tpi_stats_1, mock_centre_tpi_stats_2]


async def mock_get_tpi_stats(*_, **__):
    return [mock_tpi_stats_1, mock_tpi_stats_2]


async def mock_get_fire_centre_tpi_fuel_areas(*_, **__):
    return [mock_centre_tpi_fuel_area_1, mock_centre_tpi_fuel_area_2, mock_centre_tpi_fuel_area_3]


async def mock_get_sfms_run_datetimes(*_, **__):
    return mock_sfms_run_datetimes


async def mock_get_sfms_bounds(*_, **__):
    return [
        (2025, "actual", date(2025, 4, 3), date(2025, 9, 23)),
        (2025, "forecast", date(2025, 4, 4), date(2025, 9, 24)),
    ]


async def mock_get_sfms_bounds_no_data(*_, **__):
    await asyncio.sleep(0)
    return []


async def mock_get_most_recent_run_datetime_for_date_range(*_, **__):
    await asyncio.sleep(0)
    for_date_1 = date(2025, 8, 25)
    for_date_2 = date(2025, 8, 26)
    run_datetime = datetime(2025, 8, 25)
    run_parameter_1 = SFMSRunParameter(
        for_date=for_date_1, run_datetime=run_datetime, run_type=SFMSRunType.FORECAST
    )
    run_parameter_2 = SFMSRunParameter(
        for_date=for_date_2, run_datetime=run_datetime, run_type=SFMSRunType.FORECAST
    )
    return [run_parameter_1, run_parameter_2]


async def mock_get_all_zone_source_ids(*_, **__):
    await asyncio.sleep(0)
    return [1, 2, 3]


async def mock_get_tpi_fuel_areas(*_, **__):
    await asyncio.sleep(0)
    return [mock_tpi_fuel_area_1, mock_centre_tpi_fuel_area_2, mock_tpi_fuel_area_3]


async def mock_get_hfi_fuels_data_for_run_parameter(*_, **__):
    await asyncio.sleep(0)
    mock_fire_zone_hfi_stats = FireZoneHFIStats(min_wind_stats=[], fuel_area_stats=[])
    return HFIStatsResponse(zone_data={1: mock_fire_zone_hfi_stats})


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.mark.usefixtures("mock_jwt_decode")
@pytest.mark.parametrize(
    "status, expected_fire_centers", [(200, "test_fba_endpoint_fire_centers.json")]
)
def test_fba_endpoint_fire_centers(status, expected_fire_centers, monkeypatch):
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)

    client = TestClient(app.main.app)
    headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}

    response = client.get("/api/fba/fire-centers/", headers=headers)

    response_filename = get_complete_filename(__file__, expected_fire_centers)
    with open(response_filename) as res_file:
        expected_response = json.load(res_file)

    assert response.status_code == status
    assert response.json() == expected_response


@pytest.mark.usefixtures("mock_client_session")
@pytest.mark.parametrize(
    "endpoint",
    [
        get_fire_centres_url,
        get_fire_zone_areas_url,
        get_fire_centre_info_url,
        get_sfms_run_datetimes_url,
        get_sfms_run_bounds_url,
        get_tpi_stats_url,
    ],
)
def test_get_endpoints_unauthorized(client: TestClient, endpoint: str):
    """Forbidden to get fire zone areas when unauthorized"""

    response = client.get(endpoint)
    assert response.status_code == 401


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_fire_centers", mock_get_fire_centres)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_centres_authorized(client: TestClient):
    """Allowed to get fire centres when authorized"""
    response = client.get(get_fire_centres_url)
    assert response.status_code == 200


async def mock_hfi_thresholds(*_, **__):
    return {1: HfiThreshold(id=1, description="4000 < hfi < 10000", name="advisory")}


async def mock_sfms_fuel_types(*_, **__):
    return [
        SFMSFuelType(id=1, fuel_type_id=1, fuel_type_code="C2", description="test fuel type c2")
    ]


async def mock_zone_hfi_wind_speed(*_, **__):
    return {
        1: (
            AdvisoryHFIWindSpeed(
                id=1, advisory_shape_id=1, threshold=1, run_parameters=1, min_wind_speed=1
            ),
        )
    }


async def mock_zone_hfi_no_wind_speed(*_, **__):
    return {}


async def mock_sfms_grass_fuel_types(*_, **__):
    return [
        SFMSFuelType(
            id=12,
            fuel_type_id=12,
            fuel_type_code="O-1a/O-1b",
            description="Matted or Standing Grass",
        ),
    ]


async def mock_zone_ids_in_centre(*_, **__):
    return [1]


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_precomputed_stats_for_shape", mock_get_fire_centre_info)
@patch("app.routers.fba.get_all_hfi_thresholds_by_id", mock_hfi_thresholds)
@patch("app.routers.fba.get_all_sfms_fuel_type_records", mock_sfms_fuel_types)
@patch("app.routers.fba.get_min_wind_speed_hfi_thresholds", mock_zone_hfi_wind_speed)
@patch("app.routers.fba.get_zone_source_ids_in_centre", mock_zone_ids_in_centre)
@patch("app.routers.fba.get_fuel_type_raster_by_year", mock_get_fuel_type_raster_by_year)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_center_info_authorized(client: TestClient):
    """Allowed to get fire centre info when authorized"""
    response = client.get(get_fire_centre_info_url)
    assert response.status_code == 200
    kfc_json = response.json()["Kamloops Fire Centre"]
    assert kfc_json["1"]["fuel_area_stats"][0]["fuel_type"]["fuel_type_id"] == 1
    assert kfc_json["1"]["fuel_area_stats"][0]["threshold"]["id"] == 1
    assert math.isclose(kfc_json["1"]["fuel_area_stats"][0]["critical_hours"]["start_time"], 9.0)
    assert math.isclose(kfc_json["1"]["fuel_area_stats"][0]["critical_hours"]["end_time"], 11.0)
    assert kfc_json["1"]["fuel_area_stats"][0]["percent_curing"] is None
    assert kfc_json["1"]["min_wind_stats"][0]["threshold"]["id"] == 1
    assert math.isclose(kfc_json["1"]["fuel_area_stats"][0]["fuel_area"], 100)
    assert math.isclose(kfc_json["1"]["fuel_area_stats"][0]["area"], 50)
    assert math.isclose(kfc_json["1"]["min_wind_stats"][0]["min_wind_speed"], 1)


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_precomputed_stats_for_shape", mock_get_fire_centre_info)
@patch(
    "app.routers.fba.get_fuel_type_raster_by_year",
    mock_get_fuel_type_raster_by_year,
)
@patch("app.routers.fba.get_all_hfi_thresholds_by_id", mock_hfi_thresholds)
@patch("app.routers.fba.get_all_sfms_fuel_type_records", mock_sfms_fuel_types)
@patch("app.routers.fba.get_min_wind_speed_hfi_thresholds", mock_zone_hfi_no_wind_speed)
@patch("app.routers.fba.get_zone_source_ids_in_centre", mock_zone_ids_in_centre)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_center_info_authorized_no_min_wind_speeds(client: TestClient):
    """Allowed to get fire centre info when authorized"""
    response = client.get(get_fire_centre_info_url)
    assert response.status_code == 200
    kfc_json = response.json()["Kamloops Fire Centre"]
    assert kfc_json["1"]["fuel_area_stats"][0]["fuel_type"]["fuel_type_id"] == 1
    assert kfc_json["1"]["fuel_area_stats"][0]["threshold"]["id"] == 1
    assert math.isclose(kfc_json["1"]["fuel_area_stats"][0]["critical_hours"]["start_time"], 9.0)
    assert math.isclose(kfc_json["1"]["fuel_area_stats"][0]["critical_hours"]["end_time"], 11.0)
    assert kfc_json["1"]["fuel_area_stats"][0]["percent_curing"] is None
    assert math.isclose(kfc_json["1"]["fuel_area_stats"][0]["fuel_area"], 100)
    assert math.isclose(kfc_json["1"]["fuel_area_stats"][0]["area"], 50)
    assert kfc_json["1"]["min_wind_stats"] == []


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_precomputed_stats_for_shape", mock_get_fire_centre_info_with_grass)
@patch(
    "app.routers.fba.get_fuel_type_raster_by_year",
    mock_get_fuel_type_raster_by_year,
)
@patch("app.routers.fba.get_all_hfi_thresholds_by_id", mock_hfi_thresholds)
@patch("app.routers.fba.get_all_sfms_fuel_type_records", mock_sfms_grass_fuel_types)
@patch("app.routers.fba.get_min_wind_speed_hfi_thresholds", mock_zone_hfi_wind_speed)
@patch("app.routers.fba.get_zone_source_ids_in_centre", mock_zone_ids_in_centre)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_center_info_authorized_grass_fuel(client: TestClient):
    """Allowed to get fire centre info when authorized with grass fuel type"""
    response = client.get(get_fire_centre_info_url)
    assert response.status_code == 200
    kfc_json = response.json()["Kamloops Fire Centre"]
    assert kfc_json["1"]["fuel_area_stats"][0]["fuel_type"]["fuel_type_id"] == 12
    assert kfc_json["1"]["fuel_area_stats"][0]["threshold"]["id"] == 1
    assert math.isclose(kfc_json["1"]["fuel_area_stats"][0]["critical_hours"]["start_time"], 9.0)
    assert math.isclose(kfc_json["1"]["fuel_area_stats"][0]["critical_hours"]["end_time"], 11.0)
    assert kfc_json["1"]["fuel_area_stats"][0]["percent_curing"] == 90
    assert response.json()["Kamloops Fire Centre"]["1"]["min_wind_stats"][0]["threshold"]["id"] == 1
    assert math.isclose(kfc_json["1"]["fuel_area_stats"][0]["fuel_area"], 100)
    assert math.isclose(kfc_json["1"]["fuel_area_stats"][0]["area"], 50)
    assert math.isclose(kfc_json["1"]["min_wind_stats"][0]["min_wind_speed"], 1)


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_run_datetimes", mock_get_sfms_run_datetimes)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_sfms_run_datetimes_authorized(client: TestClient):
    """Allowed to get sfms run datetimes when authorized"""
    response = client.get(get_sfms_run_datetimes_url)
    assert response.status_code == 200
    assert response.json()[0] == datetime(
        year=2024, month=1, day=1, hour=1, tzinfo=timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_centre_tpi_stats", mock_get_centre_tpi_stats)
@patch("app.routers.fba.get_fire_centre_tpi_fuel_areas", mock_get_fire_centre_tpi_fuel_areas)
@patch("app.routers.fba.get_fuel_type_raster_by_year", mock_get_fuel_type_raster_by_year)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_centre_tpi_stats_authorized(client: TestClient):
    """Allowed to get fire zone tpi stats when authorized"""
    response = client.get(get_fire_centre_tpi_stats_url)
    square_metres = math.pow(mock_centre_tpi_stats_2.pixel_size_metres, 2)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["fire_centre_name"] == mock_fire_centre_name
    assert json_response["firezone_tpi_stats"][0]["fire_zone_id"] == 1
    assert (
        json_response["firezone_tpi_stats"][0]["valley_bottom_hfi"]
        == mock_centre_tpi_stats_1.valley_bottom * square_metres
    )
    assert (
        json_response["firezone_tpi_stats"][0]["mid_slope_hfi"]
        == mock_centre_tpi_stats_1.mid_slope * square_metres
    )
    assert (
        json_response["firezone_tpi_stats"][0]["upper_slope_hfi"]
        == mock_centre_tpi_stats_1.upper_slope * square_metres
    )
    assert (
        json_response["firezone_tpi_stats"][0]["valley_bottom_tpi"]
        == mock_centre_tpi_fuel_area_1.fuel_area
    )
    assert (
        json_response["firezone_tpi_stats"][0]["mid_slope_tpi"]
        == mock_centre_tpi_fuel_area_2.fuel_area
    )
    assert (
        json_response["firezone_tpi_stats"][0]["upper_slope_tpi"]
        == mock_centre_tpi_fuel_area_3.fuel_area
    )

    assert json_response["firezone_tpi_stats"][1]["fire_zone_id"] == 2
    assert (
        json_response["firezone_tpi_stats"][1]["valley_bottom_hfi"]
        == mock_centre_tpi_stats_2.valley_bottom * square_metres
    )
    assert (
        json_response["firezone_tpi_stats"][1]["mid_slope_hfi"]
        == mock_centre_tpi_stats_2.mid_slope * square_metres
    )
    assert (
        json_response["firezone_tpi_stats"][1]["upper_slope_hfi"]
        == mock_centre_tpi_stats_2.upper_slope * square_metres
    )
    assert json_response["firezone_tpi_stats"][1]["valley_bottom_tpi"] is None
    assert json_response["firezone_tpi_stats"][1]["mid_slope_tpi"] is None
    assert json_response["firezone_tpi_stats"][1]["upper_slope_tpi"] is None

@pytest.mark.usefixtures("mock_jwt_decode")
@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_tpi_stats", mock_get_tpi_stats)
@patch("app.routers.fba.get_fuel_type_raster_by_year", mock_get_fuel_type_raster_by_year)
@patch("app.routers.fba.get_tpi_fuel_areas", mock_get_tpi_fuel_areas)
def test_get_tpi_stats_authorized(client: TestClient):
    """Allowed to get tpi stats for run parameters when authorized"""
    response = client.get(get_tpi_stats_url)

    json_response = response.json()
    assert response.status_code == 200
    assert json_response["firezone_tpi_stats"][0]["fire_zone_id"] == 1
    assert json_response["firezone_tpi_stats"][0]["valley_bottom_hfi"] == 4
    assert json_response["firezone_tpi_stats"][0]["valley_bottom_tpi"] is None
    assert json_response["firezone_tpi_stats"][0]["mid_slope_hfi"] == 8
    assert math.isclose(json_response["firezone_tpi_stats"][0]["mid_slope_tpi"], 2.0)
    assert json_response["firezone_tpi_stats"][0]["upper_slope_hfi"] == 12
    assert json_response["firezone_tpi_stats"][0]["upper_slope_tpi"] is None
    assert json_response["firezone_tpi_stats"][1]["fire_zone_id"] == 2
    assert json_response["firezone_tpi_stats"][1]["valley_bottom_hfi"] == 4
    assert json_response["firezone_tpi_stats"][1]["valley_bottom_tpi"] is None
    assert json_response["firezone_tpi_stats"][1]["mid_slope_hfi"] == 8
    assert json_response["firezone_tpi_stats"][1]["mid_slope_tpi"] is None
    assert json_response["firezone_tpi_stats"][1]["upper_slope_hfi"] == 12
    assert json_response["firezone_tpi_stats"][1]["upper_slope_tpi"] is None


@pytest.mark.usefixtures("mock_jwt_decode")
@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_sfms_bounds", mock_get_sfms_bounds)
def test_get_sfms_run_bounds(client: TestClient):
    response = client.get(get_sfms_run_bounds_url)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["sfms_bounds"]["2025"]["actual"]["minimum"] == "2025-04-03"
    assert json_response["sfms_bounds"]["2025"]["actual"]["maximum"] == "2025-09-23"
    assert json_response["sfms_bounds"]["2025"]["forecast"]["minimum"] == "2025-04-04"
    assert json_response["sfms_bounds"]["2025"]["forecast"]["maximum"] == "2025-09-24"


@pytest.mark.usefixtures("mock_jwt_decode")
@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch(
    "app.routers.fba.get_sfms_bounds",
    mock_get_sfms_bounds_no_data,
)
def test_get_sfms_run_bounds_no_bounds(client: TestClient):
    response = client.get(get_sfms_run_bounds_url)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["sfms_bounds"] == {}


FBA_ENDPOINTS = [
    "/api/fba/fire-centers",
    "/api/fba/fire-shape-areas/forecast/2022-09-27/2022-09-27",
    "/api/fba/fire-centre-hfi-stats/forecast/2022-09-27/2022-09-27/Kamloops%20Fire%20Centre",
    "/api/fba/fire-centre-tpi-stats/forecast/2024-08-10/2024-08-10/PGFireCentre",
    "/api/fba/sfms-run-datetimes/forecast/2022-09-27",
    "/api/fba/sfms-run-bounds",
    "/api/fba/latest-sfms-run-parameters/2025-08-25/2025-08-26",
    "/api/fba/hfi-stats/forecast/2025-08-25T15:01:47.340947Z/2025-08-26",
    "/api/fba/tpi-stats/forecast/2025-08-25T15:01:47.340947Z/2025-08-26",
]


@pytest.mark.usefixtures("mock_test_idir_jwt_decode")
@pytest.mark.parametrize("endpoint", FBA_ENDPOINTS)
@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_fire_centers", mock_get_fire_centres)
@patch("app.routers.fba.get_hfi_area", mock_get_hfi_area)
@patch("app.routers.fba.get_precomputed_stats_for_shape", mock_get_fire_centre_info)
@patch("app.routers.fba.get_all_hfi_thresholds_by_id", mock_hfi_thresholds)
@patch("app.routers.fba.get_all_sfms_fuel_type_records", mock_sfms_fuel_types)
@patch("app.routers.fba.get_min_wind_speed_hfi_thresholds", mock_zone_hfi_wind_speed)
@patch("app.routers.fba.get_zone_source_ids_in_centre", mock_zone_ids_in_centre)
@patch("app.routers.fba.get_fuel_type_raster_by_year", mock_get_fuel_type_raster_by_year)
@patch("app.routers.fba.get_fire_centre_tpi_fuel_areas", mock_get_fire_centre_tpi_fuel_areas)
@patch("app.routers.fba.get_centre_tpi_stats", mock_get_centre_tpi_stats)
@patch("app.routers.fba.get_tpi_stats", mock_get_tpi_stats)
@patch("app.routers.fba.get_run_datetimes", mock_get_sfms_run_datetimes)
@patch("app.routers.fba.get_sfms_bounds", mock_get_sfms_bounds)
@patch(
    "app.routers.fba.get_most_recent_run_datetime_for_date_range",
    mock_get_most_recent_run_datetime_for_date_range,
)
@patch(
    "app.routers.fba.get_all_zone_source_ids",
    mock_get_all_zone_source_ids,
)
@patch("app.routers.fba.get_tpi_fuel_areas", mock_get_tpi_fuel_areas)
@patch("app.routers.fba.get_tpi_stats", mock_get_tpi_stats)
def test_fba_endpoints_allowed_for_test_idir(client, endpoint):
    headers = {"Authorization": "Bearer token"}
    response = client.get(endpoint, headers=headers)
    assert response.status_code == 200
