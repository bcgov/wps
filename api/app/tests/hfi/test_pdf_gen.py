import json
import os
from app.hfi.pdf_generator import generate_daily, generate_prep
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
        pdf_string = generate_daily(HFIResultResponse(**result), fire_centres)
        assert len(pdf_string) > 0


def test_gen_prep_pdf():
    """ All dailies in prep pdf data are grouped by station code and sorted by date"""
    with open(test_hfi_result, 'r') as hfi_result:
        result = json.load(hfi_result)
        pdf_string = generate_prep(HFIResultResponse(**result))
        assert len(pdf_string) > 0
