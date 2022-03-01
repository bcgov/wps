import json
from app.utils.daily_pdf_gen import generate_daily_pdf, get_jinja_area_data
from app.schemas.hfi_calc import HFIResultResponse


def test_gen_daily_pdf():
    with open('api/app/tests/utils/test_hfi_result.json', 'r') as hfi_result:
        result = json.load(hfi_result)
        assert generate_daily_pdf(HFIResultResponse(**result)) == True


def test_daily_pdf_input():
    with open('api/app/tests/utils/test_hfi_result.json', 'r') as hfi_result:
        result = json.load(hfi_result)
        get_jinja_area_data(HFIResultResponse(**result)) == True
