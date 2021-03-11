""" BDD tests for c-haines api endpoint.
"""
import os
from typing import Callable
import json
import importlib
import jsonpickle
from pytest_bdd import scenario, given, when, then
from fastapi.testclient import TestClient
import app.main
from app.tests import load_json_file, _load_json_file, get_complete_filename


def _load_text_file(module_path: str, filename: str) -> str:
    """ Load json file given a module path and a filename """
    if filename:
        with open(get_complete_filename(module_path, filename)) as file_pointer:
            return file_pointer.read()
    return None


def load_expected_response(module_path: str) -> Callable[[str], object]:
    """ Return a loader for the expected response (dict is json, otherwise text) """
    def _loader(filename: str):
        if filename and filename.endswith('.json'):
            return {'type': 'json', 'data': _load_json_file(module_path, filename)}
        return {'type': 'text', 'data': _load_text_file(module_path, filename)}
    return _loader


def _jsonpickle_patch_function(monkeypatch, module_name: str, function_name: str, json_filename: str):
    """ Patch module_name.function_name to return de-serialized json_filename """
    def mock_get_data(*_):
        filename = get_complete_filename(__file__, json_filename)
        with open(filename) as file_pointer:
            return jsonpickle.decode(file_pointer.read())

    monkeypatch.setattr(importlib.import_module(module_name), function_name, mock_get_data)


def _json_patch_function(monkeypatch, module_name: str, function_name: str, json_filename: str):
    """ Patch module_name.function_name to return de-serialized json_filename """
    def mock_get_data(*_):
        filename = get_complete_filename(__file__, json_filename)
        with open(filename) as file_pointer:
            return json.load(file_pointer)

    monkeypatch.setattr(importlib.import_module(module_name), function_name, mock_get_data)


@scenario("test_c_haines_endpoints.feature", "C-Haines endpoint testing",
          example_converters=dict(
              crud_mapping=load_json_file(__file__),
              endpoint=str,
              status_code=int,
              expected_response=load_expected_response(__file__)))
def test_c_haines():
    """ BDD Scenario for c-haines """


@given("A <crud_mapping>", target_fixture='collector')
def given_a_crud_mapping(monkeypatch, crud_mapping: dict):
    """ Mock the sql response """

    if crud_mapping:
        for item in crud_mapping:
            if item['serializer'] == "jsonpickle":
                _jsonpickle_patch_function(monkeypatch, item['module'], item['function'], item['json'])
            else:
                _json_patch_function(monkeypatch, item['module'], item['function'], item['json'])

    return {}


@when("I call <endpoint>")
def when_endpoint(collector, endpoint: str):
    """ Call the API endpoint and store the response """
    client = TestClient(app.main.app)
    collector['response'] = client.get(endpoint)


@then("I expect <status_code>")
def then_status_code(collector, status_code: int):
    """ Assert that we receive the expected status code """
    assert collector['response'].status_code == status_code


@then("The <expected_response> is matched")
def then_expected_response(collector, expected_response):
    """ Assert that the response is as expected """
    if expected_response['type'] == 'json':
        assert collector['response'].json() == expected_response['data']
    else:
        assert collector['response'].text == expected_response['data']
