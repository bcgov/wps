from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from wps_shared.schemas.sfms import FuelCodesLookup
from wps_shared.sfms.national_fuel_lookup import NATIONAL_FUEL_CODES

from wps_tools.upload_national_fuel_codes import upload_national_fuel_codes


@pytest.mark.anyio
async def test_uploads_the_national_fuel_codes_to_their_key():
    s3_client = SimpleNamespace(bucket="test-bucket", put_object=AsyncMock())

    await upload_national_fuel_codes(s3_client)

    put_kwargs = s3_client.put_object.await_args.kwargs
    assert put_kwargs["key"] == "sfms_ng/fuel/temporal/fuel_codes_lookup.json"
    assert FuelCodesLookup.model_validate_json(put_kwargs["body"]) == NATIONAL_FUEL_CODES
