import json
from app.utils.daily_pdf_gen import generate_daily_pdf
from app.schemas.hfi_calc import HFIResultResponse


def test_ros():
    with open('api/app/tests/utils/test_hfi_result.json', 'r') as hfi_result:
        result = json.load(hfi_result)
        assert generate_daily_pdf(HFIResultResponse(**result)) == True
