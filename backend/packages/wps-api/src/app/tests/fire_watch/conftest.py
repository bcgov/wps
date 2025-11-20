from datetime import datetime
import pytest
from wps_shared.db.models.fire_watch import FireWatch
from wps_shared.fuel_types import FuelTypeEnum


@pytest.fixture
def mock_fire_watch():
    """Mock FireWatch instance with a valid geometry and realistic defaults."""
    return FireWatch(
        id=1,
        burn_location="POINT(1234567 654321)",
        burn_window_start=datetime(2025, 12, 10),
        burn_window_end=datetime(2025, 12, 20),
        contact_email=["test@example.com"],
        create_timestamp=datetime(2025, 12, 15),
        create_user="unit_test_user",
        update_timestamp=datetime(2025, 12, 16),
        update_user="unit_test_user",
        fire_centre=1,
        station_code=101,
        status="active",
        title="Mock Prescribed Burn",
        fuel_type=FuelTypeEnum.C3,
        percent_conifer=20.0,
        percent_dead_fir=5.0,
        percent_grass_curing=75.0,
        temp_min=10.0,
        temp_preferred=20.0,
        temp_max=30.0,
        rh_min=20.0,
        rh_preferred=40.0,
        rh_max=60.0,
        wind_speed_min=5.0,
        wind_speed_preferred=10.0,
        wind_speed_max=20.0,
        ffmc_min=80.0,
        ffmc_preferred=88.0,
        ffmc_max=95.0,
        dmc_min=10.0,
        dmc_preferred=20.0,
        dmc_max=30.0,
        dc_min=100.0,
        dc_preferred=200.0,
        dc_max=300.0,
        isi_min=5.0,
        isi_preferred=10.0,
        isi_max=15.0,
        bui_min=40.0,
        bui_preferred=60.0,
        bui_max=80.0,
        hfi_min=0.0,
        hfi_preferred=1000.0,
        hfi_max=4000.0,
    )
