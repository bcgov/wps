from datetime import datetime, timezone

import pytest

from wps_shared.weather_models.rdps import RDPSKeyAddresser


@pytest.mark.parametrize(
    "timestamp,expected_output_key",
    [
        (
            datetime(2024, 7, 30, 10, tzinfo=timezone.utc),
            "00/precip/COMPUTED_reg_APCP_SFC_0_ps10km_20240730_10z.tif",
        ),
        (
            datetime(2024, 7, 30, 20, tzinfo=timezone.utc),
            "12/precip/COMPUTED_reg_APCP_SFC_0_ps10km_20240730_20z.tif",
        ),
    ],
)
def test_compose_computed_precip_rdps_key(timestamp, expected_output_key):
    output_precip_key = RDPSKeyAddresser().compose_computed_precip_rdps_key(timestamp)
    assert output_precip_key == expected_output_key
