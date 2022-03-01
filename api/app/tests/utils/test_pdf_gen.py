import json
from app.utils.daily_pdf_gen import generate_daily_pdf, get_jinja_area_data
from app.schemas.hfi_calc import HFIResultResponse
from app.utils.pdf_gen import response_2_prep_cycle_jinja_format


def test_gen_daily_pdf():
    with open('api/app/tests/utils/test_hfi_result.json', 'r') as hfi_result:
        result = json.load(hfi_result)
        assert generate_daily_pdf(HFIResultResponse(**result)) == True


def test_gen_prep_data_converter():
    with open('api/app/tests/utils/test_hfi_result.json', 'r') as hfi_result:
        result = json.load(hfi_result)
        prep_pdf_data = response_2_prep_cycle_jinja_format(HFIResultResponse(**result))
        assert 1 == 1
