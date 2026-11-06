"""exercise SFMS NG routing with real raster samples and a fake object store."""

import json
from datetime import date
from unittest.mock import AsyncMock, call

import numpy as np
import pytest
from app import sfms_main
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient
from osgeo import gdal
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.run_type import RunType
from wps_shared.tests.geospatial.dataset_common import create_test_dataset
from wps_shared.utils.s3_client import S3Client, get_s3_client

BASE_URL = "/api/sfms/v1/daily"
FOR_DATE = "2026-10-13"
COORDINATES = {"lat": 49.5, "lon": -123.5}
FAMILIES = {
    "fwi": ("ffmc", "dmc", "dc", "isi", "bui", "fwi", "danger_rating"),
    "fbp": ("sfc", "ros", "hfi", "tfc", "cfb", "fire_area_30min", "fmc"),
    "weather": (
        "temperature",
        "relative_humidity",
        "wind_speed",
        "wind_direction",
        "precipitation",
        "grass_curing",
    ),
}
PARAMETERS = [
    (family, parameter) for family, parameters in FAMILIES.items() for parameter in parameters
]
RUN_TYPES = (None, "actual", "forecast")


def manifest_key(run_type="actual", hour="00"):
    return (
        f"sfms_ng/runs/{run_type}/2026/10/13/"
        f"target-{FOR_DATE}_run-2026-10-14T{hour}-00-00.000000Z.json"
    )


def archive_key(run_type="actual"):
    return f"sfms_ng/static/archive/percent_grass_curing/{run_type}-hash.tif"


def manifest_bytes(run_type="actual", status="success", grass_curing="recorded"):
    static_rasters = {}
    if grass_curing == "recorded":
        static_rasters["grass_curing"] = archive_key(run_type)
    return json.dumps(
        {
            "version": 1,
            "for_date": FOR_DATE,
            "run_type": run_type,
            "status": status,
            "input": {"static_rasters": static_rasters},
        }
    ).encode()


def expected_key(parameter, run_type="actual"):
    if parameter == "fmc":
        return "sfms_ng/static/fmc/2026/10/13/fmc_20261013.tif"
    if parameter == "grass_curing":
        return archive_key(run_type)
    return f"sfms_ng/{run_type}/2026/10/13/{parameter}_20261013.tif"


def s3_error(code):
    return ClientError({"Error": {"Code": code}}, "GetObject")


@pytest.fixture
def raster_bytes(tmp_path):
    dataset = create_test_dataset("sample", 2, 2, (-124, -122, 48, 50), 4326, no_data_value=-9999)
    dataset.GetRasterBand(1).WriteArray(np.array([[42, -9999], [np.nan, np.inf]]))
    path = tmp_path / "sample.tif"
    output = gdal.GetDriverByName("GTiff").CreateCopy(str(path), dataset)
    output.Close()
    dataset.Close()
    return path.read_bytes()


@pytest.fixture
def storage(raster_bytes):
    objects = {}
    for run_type in ("actual", "forecast"):
        objects[manifest_key(run_type)] = manifest_bytes(run_type)
        for _, parameter in PARAMETERS:
            objects[expected_key(parameter, run_type)] = raster_bytes

    def read(key):
        if key not in objects:
            raise s3_error("NoSuchKey")
        return objects[key]

    async def stream(key, byte_range):
        body = read(key)
        headers = {"ContentType": "image/tiff", "ContentLength": len(body), "ETag": '"test"'}
        if byte_range:
            assert byte_range == "bytes=0-3"
            headers["ContentRange"] = f"bytes 0-3/{len(body)}"
            body = body[:4]

        async def chunks():
            yield body

        return chunks(), headers

    async def list_objects(**kwargs):
        return {
            "Contents": [
                {"Key": key} for key in sorted(objects) if key.startswith(kwargs["Prefix"])
            ]
        }

    s3_client = S3Client(server="test", user_id="test", secret_key="test", bucket="test")
    s3_client.read_object = AsyncMock(side_effect=read)
    s3_client.stream = AsyncMock(side_effect=stream)
    s3_client.client = AsyncMock()
    s3_client.client.list_objects_v2.side_effect = list_objects
    return s3_client, objects


@pytest.fixture
def client(storage):
    s3_client, _ = storage
    overrides = sfms_main.api.dependency_overrides
    overrides[get_s3_client] = lambda: s3_client
    yield TestClient(sfms_main.app)
    overrides.pop(get_s3_client, None)


@pytest.mark.parametrize("family,parameter", PARAMETERS)
@pytest.mark.parametrize("run_type", RUN_TYPES)
def test_downloads_each_parameter(client, storage, raster_bytes, family, parameter, run_type):
    params = {} if run_type is None else {"run_type": run_type}
    response = client.get(f"{BASE_URL}/{family}/{FOR_DATE}/{parameter}", params=params)

    assert response.status_code == 200
    assert response.content == raster_bytes
    assert response.headers["content-type"] == "image/tiff"
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["etag"] == '"test"'
    assert response.headers["content-length"] == str(len(raster_bytes))
    storage[0].stream.assert_awaited_once_with(expected_key(parameter, run_type or "actual"), None)


@pytest.mark.parametrize("family,parameter", PARAMETERS)
@pytest.mark.parametrize("run_type", RUN_TYPES)
def test_samples_each_parameter(client, storage, family, parameter, run_type):
    params = {**COORDINATES}
    if run_type:
        params["run_type"] = run_type
    response = client.get(f"{BASE_URL}/{family}/{FOR_DATE}/{parameter}/value", params=params)

    assert response.status_code == 200
    assert response.json() == {
        "date": FOR_DATE,
        "run_type": run_type or "actual",
        "parameter": parameter,
        "latitude": COORDINATES["lat"],
        "longitude": COORDINATES["lon"],
        "value": 42.0,
    }
    assert storage[0].read_object.await_args == call(expected_key(parameter, run_type or "actual"))


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("run_type", RUN_TYPES)
def test_samples_family(client, storage, family, run_type):
    params = {**COORDINATES}
    if run_type:
        params["run_type"] = run_type
    response = client.get(f"{BASE_URL}/{family}/{FOR_DATE}/values", params=params)

    assert response.status_code == 200
    assert response.json() == {
        "date": FOR_DATE,
        "run_type": run_type or "actual",
        "latitude": COORDINATES["lat"],
        "longitude": COORDINATES["lon"],
        **dict.fromkeys(FAMILIES[family], 42.0),
    }
    storage[0].read_object.assert_has_awaits(
        [call(expected_key(parameter, run_type or "actual")) for parameter in FAMILIES[family]],
        any_order=True,
    )


@pytest.mark.parametrize(
    "family,parameter", [("fwi", "fwi"), ("fbp", "fmc"), ("weather", "grass_curing")]
)
def test_range_download(client, storage, raster_bytes, family, parameter):
    response = client.get(
        f"{BASE_URL}/{family}/{FOR_DATE}/{parameter}", headers={"Range": "bytes=0-3"}
    )
    assert response.status_code == 206
    assert response.content == raster_bytes[:4]
    assert response.headers["content-range"] == f"bytes 0-3/{len(raster_bytes)}"
    assert response.headers["content-length"] == "4"
    assert response.headers["content-disposition"].endswith(
        expected_key(parameter).rsplit("/", 1)[1]
    )
    storage[0].stream.assert_awaited_once_with(expected_key(parameter), "bytes=0-3")


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("suffix", ["value", "values"])
@pytest.mark.parametrize("lat,lon", [(0, 0), (49.5, -122.5), (48.5, -123.5), (48.5, -122.5)])
def test_samples_null_outside_extent_on_nodata_or_nonfinite(client, family, suffix, lat, lon):
    parameter = FAMILIES[family][0]
    path = "values" if suffix == "values" else f"{parameter}/value"
    response = client.get(f"{BASE_URL}/{family}/{FOR_DATE}/{path}", params={"lat": lat, "lon": lon})
    assert response.status_code == 200
    data = response.json()
    if suffix == "value":
        assert data["value"] is None
    else:
        assert all(data[parameter] is None for parameter in FAMILIES[family])


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("operation", ["download", "value", "values"])
@pytest.mark.parametrize("code,status", [("NoSuchKey", 404), ("InternalError", 502)])
def test_object_store_errors(client, storage, family, operation, code, status):
    parameter = FAMILIES[family][0]
    path = parameter if operation == "download" else f"{parameter}/value"
    if operation == "values":
        path = "values"
    method = storage[0].stream if operation == "download" else storage[0].read_object
    method.side_effect = s3_error(code)
    response = client.get(f"{BASE_URL}/{family}/{FOR_DATE}/{path}", params=COORDINATES)
    assert response.status_code == status


@pytest.mark.parametrize("family", FAMILIES)
def test_family_request_fails_if_one_raster_is_missing(client, storage, family):
    del storage[1][expected_key(FAMILIES[family][-1])]
    response = client.get(f"{BASE_URL}/{family}/{FOR_DATE}/values", params=COORDINATES)
    assert response.status_code == 404


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("suffix", ["", "/value"])
@pytest.mark.parametrize("parameter", ["invalid", "hffmc"])
def test_rejects_invalid_parameters(client, family, suffix, parameter):
    response = client.get(f"{BASE_URL}/{family}/{FOR_DATE}/{parameter}{suffix}", params=COORDINATES)
    assert response.status_code == 422


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("operation", ["download", "value", "values"])
@pytest.mark.parametrize("invalid", ["date", "run_type"])
def test_rejects_invalid_date_or_run_type(client, family, operation, invalid):
    for_date = "2026-02-30" if invalid == "date" else FOR_DATE
    params = {**COORDINATES, "run_type": "invalid" if invalid == "run_type" else "actual"}
    parameter = FAMILIES[family][0]
    path = parameter if operation == "download" else f"{parameter}/value"
    if operation == "values":
        path = "values"
    assert client.get(f"{BASE_URL}/{family}/{for_date}/{path}", params=params).status_code == 422


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("operation", ["value", "values"])
@pytest.mark.parametrize(
    "params", [{}, {"lat": 91, "lon": 0}, {"lat": 0, "lon": -181}, {"lat": "nan", "lon": 0}]
)
def test_rejects_invalid_coordinates(client, family, operation, params):
    path = "values" if operation == "values" else f"{FAMILIES[family][0]}/value"
    assert client.get(f"{BASE_URL}/{family}/{FOR_DATE}/{path}", params=params).status_code == 422


@pytest.mark.parametrize("run_type", ["actual", "forecast"])
def test_grass_curing_selects_newest_success_across_listing_pages(client, storage, run_type):
    s3_client, objects = storage
    oldest = manifest_key(run_type)
    newest_success = manifest_key(run_type, "01")
    newest_failure = manifest_key(run_type, "02")
    objects[oldest] = manifest_bytes(run_type, grass_curing="missing")
    objects[newest_success] = manifest_bytes(run_type)
    objects[newest_failure] = manifest_bytes(run_type, status="failed")
    listing = s3_client.client.list_objects_v2
    listing.side_effect = [
        {"Contents": [{"Key": oldest}], "IsTruncated": True, "NextContinuationToken": "next"},
        {"Contents": [{"Key": newest_success}, {"Key": newest_failure}], "IsTruncated": False},
    ]

    response = client.get(
        f"{BASE_URL}/weather/{FOR_DATE}/grass_curing/value",
        params={**COORDINATES, "run_type": run_type},
    )
    assert response.status_code == 200
    assert response.json()["value"] == 42
    s3_client.read_object.assert_has_awaits(
        [call(newest_failure), call(newest_success), call(archive_key(run_type))]
    )
    prefix = f"sfms_ng/runs/{run_type}/2026/10/13/target-{FOR_DATE}_run-"
    listing.assert_has_awaits(
        [
            call(Bucket="test", Prefix=prefix, MaxKeys=1000),
            call(Bucket="test", Prefix=prefix, MaxKeys=1000, ContinuationToken="next"),
        ]
    )


@pytest.mark.parametrize("run_type", ["actual", "forecast"])
@pytest.mark.parametrize("missing", ["manifest", "successful_run", "reference", "archive"])
@pytest.mark.parametrize("operation", ["download", "value", "values"])
def test_grass_curing_returns_404_without_archived_run_input(
    client, storage, run_type, missing, operation
):
    _, objects = storage
    if missing == "manifest":
        del objects[manifest_key(run_type)]
    elif missing == "successful_run":
        objects[manifest_key(run_type)] = manifest_bytes(run_type, status="failed")
    elif missing == "reference":
        objects[manifest_key(run_type, "01")] = manifest_bytes(run_type, grass_curing="missing")
    else:
        del objects[archive_key(run_type)]

    path = "grass_curing" if operation == "download" else "grass_curing/value"
    if operation == "values":
        path = "values"
    response = client.get(
        f"{BASE_URL}/weather/{FOR_DATE}/{path}", params={**COORDINATES, "run_type": run_type}
    )
    assert response.status_code == 404


@pytest.mark.parametrize(
    "failure",
    ["listing", "reading", "invalid_json", "schema", "date_mismatch", "run_type_mismatch"],
)
def test_grass_curing_returns_502_for_object_store_or_manifest_errors(client, storage, failure):
    s3_client, objects = storage
    if failure == "listing":
        s3_client.client.list_objects_v2.side_effect = s3_error("InternalError")
    elif failure == "reading":
        s3_client.read_object.side_effect = s3_error("InternalError")
    elif failure == "invalid_json":
        objects[manifest_key()] = b"not json"
    else:
        body = json.loads(manifest_bytes())
        if failure == "schema":
            body["version"] = 99
        elif failure == "date_mismatch":
            body["for_date"] = "2026-10-12"
        else:
            body["run_type"] = "forecast"
        objects[manifest_key()] = json.dumps(body).encode()

    response = client.get(f"{BASE_URL}/weather/{FOR_DATE}/grass_curing/value", params=COORDINATES)
    assert response.status_code == 502


def test_openapi_documents_sources_types_and_range_responses(client):
    schema = client.get("/api/openapi.json").json()
    paths = {
        path: item for path, item in schema["paths"].items() if path.startswith("/sfms/v1/daily/")
    }
    assert len(paths) == 9
    for path, item in paths.items():
        operation = item["get"]
        assert "Source system: SFMS NG" in operation["description"]
        params = {parameter["name"]: parameter["schema"] for parameter in operation["parameters"]}
        assert params["run_type"]["default"] == "actual"
        assert params["for_date"]["format"] == "date"
        if "{parameter}" in path:
            parameter_schema = params["parameter"]["$ref"].rsplit("/", 1)[1]
            family = path.split("/")[4]
            assert set(schema["components"]["schemas"][parameter_schema]["enum"]) == set(
                FAMILIES[family]
            )
        if path.endswith("/{parameter}"):
            assert set(operation["responses"]["200"]["content"]) == {"image/tiff"}
            assert "206" in operation["responses"]
        assert {"404", "422", "502"} <= operation["responses"].keys()
    legacy = schema["paths"]["/sfms/daily-fwi/{for_date}/{parameter}"]["get"]
    assert "legacy SFMS" in legacy["description"]
    assert not any(path.startswith("/sfms/v1/hourly") for path in schema["paths"])


def test_main_api_does_not_serve_ng_rasters():
    from app import main

    client = TestClient(main.app)
    assert client.get(f"{BASE_URL}/fwi/{FOR_DATE}/fwi").status_code == 404


@pytest.mark.parametrize("run_type", [RunType.ACTUAL, RunType.FORECAST])
def test_manifest_prefix_matches_existing_manifest_keys(run_type):
    addresser = SFMSNGRasterAddresser()
    assert addresser.get_run_manifest_prefix(run_type, date.fromisoformat(FOR_DATE)) == (
        f"sfms_ng/runs/{run_type.value}/2026/10/13/target-{FOR_DATE}_run-"
    )
