import json
import os
from datetime import date, datetime
from jinja2 import Environment, FunctionLoader
from app.hfi.pdf_generator import generate_pdf, get_pdf_filename
from app.hfi.pdf_template import get_template
from app.schemas.hfi_calc import (FireCentre,
                                  HFIResultResponse)
from app.schemas.hfi_calc import HFIResultResponse

test_hfi_result = os.path.join(os.path.dirname(__file__), 'test_hfi_result.json')
test_fcs = os.path.join(os.path.dirname(__file__), 'test_fire_centres.json')


def test_generate_pdf():
    jinja_env = Environment(loader=FunctionLoader(get_template), autoescape=True)
    with open(test_hfi_result, 'r') as hfi_result, open(test_fcs, 'r') as fcs:
        result = json.load(hfi_result)
        fc_dict = json.load(fcs)
        fire_centres = []
        for fc_json in fc_dict['fire_centres']:
            fc = FireCentre(**fc_json)
            fire_centres.append(fc)

        pdf_bytes, pdf_filename = generate_pdf(HFIResultResponse(**result), fire_centres, 'wps',
                                               datetime.fromisocalendar(2022, 2, 2), jinja_env)
        assert len(pdf_bytes) > 0
        assert pdf_filename is not None


def test_pdf_filename():
    res = get_pdf_filename('Kamloops', date.fromisocalendar(2022, 2, 2), 'wps')
    assert res == 'Kamloops_HFICalculator_2022-01-11_WPS.pdf'
