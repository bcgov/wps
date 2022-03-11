import datetime
import json
import os
from app.hfi.daily_pdf_gen import generate_daily_pdf
from app.hfi.pdf_data_formatter import response_2_prep_cycle_jinja_format
from app.hfi.prep_pdf_gen import generate_prep_pdf
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


def test_gen_prep_data_converter():
    """ All dailies in prep pdf data are grouped by station code and sorted by date"""
    with open(test_hfi_result, 'r') as hfi_result:
        result = json.load(hfi_result)
        prep_pdf_data = response_2_prep_cycle_jinja_format(HFIResultResponse(**result))

        # List of dates for prep period
        dates = []
        for area in prep_pdf_data:
            for code, dailies in area.dailies.items():
                for daily in dailies:
                    date_obj = datetime.datetime.strptime(str(daily.date), '%Y-%m-%d %H:%M:%S%z')
                    formatted_date_string = str(date_obj.strftime("%A %B, %d, %Y"))
                    dates.append(formatted_date_string)
                break
            break

        pdf_bytes = generate_prep_pdf(prep_pdf_data, dates)
        assert len(pdf_bytes) > 0
