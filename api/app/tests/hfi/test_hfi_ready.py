from fastapi.testclient import TestClient
import pytest
from datetime import datetime
import app
import json
from app.db.models.hfi_calc import HFIRequest, HFIReady

request_json = {
    "selected_prep_date": "2020-05-21",
    "start_date": "2020-05-21",
    "end_date": "2020-05-26",
    "planning_area_station_info": {
        "1": [
                {
                    "station_code": 230,
                    "selected": True,
                    "fuel_type_id": 1
                }
        ]
    },
    "selected_fire_center_id": 1,
    "planning_area_hfi_results": [],
    "planning_area_fire_starts": {}
}
mock_hfi_request = HFIRequest(id=1, request=json.dumps(request_json))


ready_state_json = {
    "hfi_request_id": 1,
    "planning_area_id": 1,
    "ready": False,
    "create_user": 'test',
    "create_timestamp": datetime.fromtimestamp(1560130969).isoformat(),
    "update_user": 'test',
    "update_timestamp": datetime.fromtimestamp(1560217369).isoformat()
}
mock_latest_ready_records = [HFIReady(id=1, **ready_state_json)]


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.mark.usefixtures('mock_jwt_decode')
def test_get_all_ready_records(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """ Basic check for retrieving ready records"""
    monkeypatch.setattr(app.routers.hfi_calc, 'get_most_recent_updated_hfi_request',
                        lambda *_: mock_hfi_request)
    monkeypatch.setattr(app.routers.hfi_calc, 'get_latest_hfi_ready_records', lambda *_: mock_latest_ready_records)

    response = client.get("/api/hfi-calc/fire_centre/5/2022-05-01/2022-05-01/ready")
    assert response.status_code == 200

    ready_states = json.loads(response.text)
    assert ready_states['ready_states'][0]['hfi_request_id'] == mock_hfi_request.id


@pytest.mark.usefixtures('mock_jwt_decode')
def test_get_all_ready_records_no_hfi_request(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """ Basic check for retrieving ready records when there is no hfi_request"""
    monkeypatch.setattr(app.routers.hfi_calc, 'get_most_recent_updated_hfi_request',
                        lambda *_: None)
    monkeypatch.setattr(app.routers.hfi_calc, 'get_latest_hfi_ready_records', lambda *_: [])

    response = client.get("/api/hfi-calc/fire_centre/5/2022-05-01/2022-05-01/ready")
    assert response.status_code == 200

    ready_states = json.loads(response.text)
    assert len(ready_states['ready_states']) == 0


def test_get_all_ready_records_unauthorized(client: TestClient):
    """ Authentication is required to request ready records """
    response = client.get("/api/hfi-calc/fire_centre/5/2022-05-01/2022-05-01/ready")
    assert response.status_code == 401


def test_toggle_ready_authorized(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """ set_hfi_ready_record role required for toggling ready state"""
    class MockJWTDecodeWithRole:
        """ Mock pyjwt module with role """

        def __init__(self, role):
            self.decoded_token = {
                "preferred_username": "test_username",
                "resource_access": {
                    "wps-web": {
                        "roles": [
                            role
                        ]
                    }
                }}

        def __getitem__(self, key):
            return self.decoded_token[key]

        def get(self, key, _):
            "Returns the mock decoded token"
            return self.decoded_token[key]

        def decode(self):
            "Returns the mock decoded token"
            return self.decoded_token

    def mock_fire_start_role_function(*_, **__):  # pylint: disable=unused-argument
        return MockJWTDecodeWithRole('hfi_set_ready_state')

    monkeypatch.setattr("jwt.decode", mock_fire_start_role_function)
    monkeypatch.setattr(app.routers.hfi_calc, 'toggle_ready', lambda *_: HFIReady(id=1, **ready_state_json))

    response = client.post(f'/api/hfi-calc/planning_area/{1}/hfi_request/{1}/ready')
    assert response.status_code == 200


def test_toggle_ready_unauthorized(client: TestClient):
    """ set_hfi_ready_record role required for toggling ready state"""
    response = client.post(f'/api/hfi-calc/planning_area/{1}/hfi_request/{1}/ready')
    assert response.status_code == 401
