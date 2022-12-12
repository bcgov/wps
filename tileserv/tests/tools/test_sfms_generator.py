from datetime import date
from tileserv.tools.sfms_generator import get_forecast_dates

dec_1_2022 = date.fromisoformat("2022-12-01")
dec_2_2022 = date.fromisoformat("2022-12-02")
dec_3_2022 = date.fromisoformat("2022-12-03")
dec_4_2022 = date.fromisoformat("2022-12-04")


def test_get_filenames_lowercase():
    res = get_forecast_dates(dec_1_2022)

    assert res[0] == dec_1_2022
    assert res[1] == dec_2_2022
    assert res[2] == dec_3_2022
    assert res[3] == dec_4_2022
