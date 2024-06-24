from datetime import datetime, timezone
from app.weather_models.rdps_filename_marshaller import parse_rdps_filename, compose_rdps_filename


def test_parse_filename_ok():
    (start_date, run_hour, forecast_hour) = parse_rdps_filename("CMC_reg_APCP_SFC_0_ps10km_2024062412_P001.grib2")
    assert start_date == "20240624"
    assert run_hour == "12"
    assert forecast_hour == "001"


def test_compose_rdps_filename_ok():
    start_date = datetime(2024, 6, 24, tzinfo=timezone.utc)
    res = compose_rdps_filename(start_date, 12, 1)
    assert res == "CMC_reg_APCP_SFC_0_ps10km_2024062412_P001.grib2"
