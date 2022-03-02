from functools import reduce
import json
from app.utils.daily_pdf_gen import generate_daily_pdf
from app.utils.pdf_gen import generate_prep_pdf
from app.schemas.hfi_calc import HFIResultResponse
from operator import attrgetter
from app.utils.pdf_data_formatter import (response_2_daily_jinja_format,
                                          response_2_prep_cycle_jinja_format)


def test_gen_daily_pdf():
    with open('api/app/tests/utils/test_hfi_result.json', 'r') as hfi_result:
        result = json.load(hfi_result)
        assert generate_daily_pdf(HFIResultResponse(**result)) == True


def test_gen_prep_data_converter():
    """ All dailies in prep pdf data are grouped by station code and sorted by date"""
    with open('api/app/tests/utils/test_hfi_result.json', 'r') as hfi_result:
        result = json.load(hfi_result)
        prep_pdf_data = response_2_prep_cycle_jinja_format(HFIResultResponse(**result))
        assert 1 == 1
        dailies_by_code = []
        for data in prep_pdf_data:
            # locally sorted by station code
            assert data.dailies == sorted(data.dailies, key=attrgetter('code'))

        all_dailies = reduce(list.__add__, list(map(lambda x: [x.dailies[0]], prep_pdf_data)))
        # globally sorted by date
        assert all_dailies == sorted(all_dailies, key=attrgetter('date'))
        generate_prep_pdf(prep_pdf_data)


def test_gen_daily_data_converter():
    """ All dailies in prep pdf data are grouped planning area and keyed by date"""
    with open('api/app/tests/utils/test_hfi_result.json', 'r') as hfi_result:
        result = json.load(hfi_result)
        daily_pdf_data = response_2_daily_jinja_format(HFIResultResponse(**result))
