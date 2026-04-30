import pytest
from wps_weather.utils import parse_date_and_run, s3_key_from_eccc_path

test_prefix = "test_prefix"


def test_s3_key_from_eccc_path():
    eccc_path = "https://dd.weather.gc.ca/20260205/WXO-DD/model_rdps/10km/12/002/20260205T00Z_MSC_RDPS_AbsoluteVorticity_IsbL-0500_RLatLon0.09_PT002H.grib2"
    s3_key = s3_key_from_eccc_path(test_prefix, eccc_path)

    # we want the output to be {prefix}/{date}/{everything after WX0-DD}

    assert (
        s3_key
        == "test_prefix/20260205/model_rdps/10km/12/002/20260205T00Z_MSC_RDPS_AbsoluteVorticity_IsbL-0500_RLatLon0.09_PT002H.grib2"
    )


def test_s3_key_from_eccc_path_raises_error():
    # missing WX0-DD (which should never really happen unless env canada datamart changes)
    eccc_path = "https://dd.weather.gc.ca/20260205/model_rdps/10km/12/002/20260205T00Z_MSC_RDPS_AbsoluteVorticity_IsbL-0500_RLatLon0.09_PT002H.grib2"

    with pytest.raises(ValueError):
        s3_key_from_eccc_path(test_prefix, eccc_path)


def test_parse_date_and_run():
    date, run = parse_date_and_run(
        "20260205T00Z_MSC_RDPS_AbsoluteVorticity_IsbL-0500_RLatLon0.09_PT002H.grib2"
    )
    assert date == "20260205"
    assert run == "00"


def test_parse_date_and_run_cmc_format_00z():
    date, run = parse_date_and_run("CMC_glb_HGT_ISBL_500_latlon.15x.15_2026042100_P000.grib2")
    assert date == "20260421"
    assert run == "00"


def test_parse_date_and_run_cmc_format_12z():
    date, run = parse_date_and_run(
        "CMC_glb_APCP-Accum12h_SFC_0_latlon.15x.15_2026042112_P012.grib2"
    )
    assert date == "20260421"
    assert run == "12"


def test_parse_date_and_run_raises():
    with pytest.raises(ValueError):
        parse_date_and_run("CMC_glb_HGT_ISBL_500_latlon.15x.15_baddate_P000.grib2")
