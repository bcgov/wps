import json
import os
from app.utils.daily_pdf_gen import generate_daily_pdf
from app.schemas.hfi_calc import HFIResultResponse
from app.schemas.hfi_calc import FireCentre, HFIResultResponse

test_hfi_result = os.path.join(os.path.dirname(__file__), 'test_hfi_result.json')
test_fcs = os.path.join(os.path.dirname(__file__), 'test_fire_centres.json')


def test_gen_daily_pdf():
    with open(test_hfi_result, 'r') as hfi_result, open(test_fcs, 'r') as fcs:
        result = json.load(hfi_result)
        fc_dict = json.load(fcs)
        fire_centres = []
        for fc_json in fc_dict['fire_centres']:
            fc = FireCentre(**fc_json)
            fire_centres.append(fc)
        pdf_bytes = generate_daily_pdf(HFIResultResponse(**result), fire_centres)
        assert len(pdf_bytes) > 0
