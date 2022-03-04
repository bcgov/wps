import json
from app.utils.daily_pdf_gen import generate_daily_pdf
from app.schemas.hfi_calc import HFIResultResponse
from app.schemas.hfi_calc import FireCentre, HFIResultResponse


def test_gen_daily_pdf():
    with open('api/app/tests/utils/test_hfi_result.json', 'r') as hfi_result, open('api/app/tests/utils/test_fire_centres.json') as fcs:
        result = json.load(hfi_result)
        fc_dict = json.load(fcs)
        fire_centres = []
        for fc_json in fc_dict['fire_centres']:
            fc = FireCentre(**fc_json)
            fire_centres.append(fc)
        assert generate_daily_pdf(HFIResultResponse(**result), fire_centres) == True
