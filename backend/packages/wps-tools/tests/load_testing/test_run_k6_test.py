from pathlib import Path

import pytest

from wps_tools.load_testing.run_k6_test import (
    build_scenario_payload,
    derive_test_names,
    extract_stack_outputs,
    is_terminal_status,
    sanitize_test_id,
    sign_request,
)


def test_build_scenario_payload():
    payload = build_scenario_payload(
        test_id="my-test-1234",
        test_name="my-test",
        test_description="a test",
        region="ca-central-1",
        task_count=2,
        concurrency=10,
        ramp_up="30s",
        hold_for="2m",
        script_file_name="my-test-1234.js",
    )

    assert payload["testId"] == "my-test-1234"
    assert payload["testType"] == "k6"
    assert payload["fileType"] == "script"
    assert payload["testTaskConfigs"] == [{"region": "ca-central-1", "taskCount": 2, "concurrency": 10}]

    [execution] = payload["testScenario"]["execution"]
    assert execution["executor"] == "k6"
    assert execution["ramp-up"] == "30s"
    assert execution["hold-for"] == "2m"
    assert execution["scenario"] == "my-test"

    assert payload["testScenario"]["scenarios"] == {"my-test": {"script": "my-test-1234.js"}}
    assert payload["regionalTaskDetails"] == {"ca-central-1": {"dltAvailableTasks": 2}}


def test_is_terminal_status():
    assert is_terminal_status(None) is False
    assert is_terminal_status("complete") is True
    assert is_terminal_status("success") is True
    assert is_terminal_status("failed") is True
    assert is_terminal_status("cancelled") is True
    assert is_terminal_status("COMPLETE") is True
    assert is_terminal_status("running") is False
    assert is_terminal_status("pending") is False
    assert is_terminal_status("provisioning") is False
    assert is_terminal_status("queued") is False
    assert is_terminal_status("cleaning up") is False
    assert is_terminal_status("parsing results") is False
    assert is_terminal_status("some-unknown-future-status") is False


def test_sanitize_test_id_replaces_disallowed_characters():
    assert sanitize_test_id("smoke_test-1786402928") == "smoke-test-1786402928"
    assert sanitize_test_id("already-valid-123") == "already-valid-123"


def test_derive_test_names_sanitizes_script_stem():
    test_id, test_name, script_file_name = derive_test_names(Path("smoke_test.js"), test_id=None, test_name=None)

    assert "_" not in test_id
    assert test_id.startswith("smoke-test-")
    assert script_file_name == f"{test_id}.js"


def test_derive_test_names_uses_provided_values():
    test_id, test_name, script_file_name = derive_test_names(
        Path("load-test.js"), test_id="explicit-id", test_name="explicit-name"
    )

    assert test_id == "explicit-id"
    assert test_name == "explicit-name"
    assert script_file_name == "explicit-id.js"


def test_derive_test_names_defaults_from_script_name():
    test_id, test_name, script_file_name = derive_test_names(Path("load-test.js"), test_id=None, test_name=None)

    assert test_id.startswith("load-test-")
    assert test_name == test_id
    assert script_file_name == f"{test_id}.js"


def test_extract_stack_outputs():
    outputs = {
        "DLTApiEndpointD98B09AC": "https://example.execute-api.ca-central-1.amazonaws.com/prod",
        "ScenariosBucket": "my-scenarios-bucket",
    }

    api_endpoint, scenarios_bucket = extract_stack_outputs(outputs)

    assert api_endpoint == "https://example.execute-api.ca-central-1.amazonaws.com/prod"
    assert scenarios_bucket == "my-scenarios-bucket"


def test_extract_stack_outputs_missing_raises():
    with pytest.raises(RuntimeError):
        extract_stack_outputs({"ScenariosBucket": "my-scenarios-bucket"})

    with pytest.raises(RuntimeError):
        extract_stack_outputs({"DLTApiEndpointD98B09AC": "https://example.com"})


def test_sign_request_produces_sigv4_authorization_header():
    credentials = {
        "idToken": "unused",
        "awsAccessKeyId": "AKIAFAKEEXAMPLE",
        "awsSecretAccessKey": "fakesecret",
        "awsSessionToken": "faketoken",
    }

    headers = sign_request(
        "POST",
        "https://example.execute-api.ca-central-1.amazonaws.com/prod/scenarios",
        "ca-central-1",
        credentials,
        b'{"testId": "my-test"}',
    )

    assert headers["Authorization"].startswith("AWS4-HMAC-SHA256 Credential=AKIAFAKEEXAMPLE/")
    assert "ca-central-1/execute-api" in headers["Authorization"]
    assert headers["X-Amz-Security-Token"] == "faketoken"
    assert "X-Amz-Date" in headers
