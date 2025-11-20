import os
import json
import importlib
import pytest
from aiohttp import ClientSession
from fastapi.testclient import TestClient
import app.main
from app.tests import load_json_file, load_sqlalchemy_response_from_json
from wps_shared.tests.common import default_mock_client_get


def _patch_function(monkeypatch, module_name: str, function_name: str, json_filename: str):
    """Patch module_name.function_name to return de-serialized json_filename"""

    def mock_get_data(*_):
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dirname, json_filename)
        return load_sqlalchemy_response_from_json(filename)

    monkeypatch.setattr(importlib.import_module(module_name), function_name, mock_get_data)


@pytest.mark.parametrize(
    "codes, endpoint, crud_mapping, expected_status_code, expected_response_file",
    [
        ([322], "/api/weather_models/GDPS/predictions/summaries/", "test_models_predictions_summaries_crud_mappings.json", 200, "test_models_predictions_summaries_response.json"),
        (
            [322, 838],
            "/api/weather_models/GDPS/predictions/summaries/",
            "test_models_predictions_summaries_multiple_crud_mappings.json",
            200,
            "test_models_predictions_summaries_response_multiple.json",
        ),
        (
            [838],
            "/api/weather_models/GDPS/predictions/most_recent/",
            "test_models_predictions_most_recent_GDPS_[838]_crud_mappings.json",
            200,
            "test_models_predictions_most_recent_GDPS_[838]_response.json",
        ),
        (
            [838, 209],
            "/api/weather_models/GDPS/predictions/most_recent/",
            "test_models_predictions_most_recent_RDPS_[838, 209]_crud_mappings.json",
            200,
            "test_models_predictions_most_recent_RDPS_[838, 209]_response.json",
        ),
        (
            [956],
            "/api/weather_models/GDPS/predictions/most_recent/",
            "test_models_predictions_most_recent_GDPS_[956]_crud_mappings.json",
            200,
            "test_models_predictions_most_recent_GDPS_[956]_response.json",
        ),
    ],
)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_successful_model_endpoint_calls(codes, endpoint, crud_mapping, expected_status_code, expected_response_file, monkeypatch):
    with open(os.path.join(os.path.dirname(__file__), crud_mapping), "r", encoding="utf-8") as tmp:
        for item in json.load(tmp):
            _patch_function(monkeypatch, item["module"], item["function"], item["json"])

    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)

    client = TestClient(app.main.app)
    response = client.post(endpoint, headers={"Authorization": "Bearer token"}, json={"stations": codes})

    assert response.status_code == expected_status_code
    expected_response = load_json_file(__file__)(expected_response_file)
    assert response.json() == expected_response
