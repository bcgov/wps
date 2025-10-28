import gzip
import json
import pytest
import numpy as np
from datetime import datetime

from app.c_haines.c_haines_index import CHainesGenerator, calculate_c_haines_index
from app.c_haines.severity_index import (
    generate_severity_data,
    make_model_run_base_url,
    make_model_run_download_urls,
    make_model_run_filename,
    open_gdal,
    re_project_and_classify_geojson,
)
from app.tests import get_complete_filename


@pytest.mark.parametrize(
    "t_850, t_700, dp_850, c_haines",
    [(27.5, 12, -1, 4.416666666666667), (13.4, 0, 2.4, 4.5)],
)
def test_calculate_c_haines(t_850, t_700, dp_850, c_haines):
    calculated = calculate_c_haines_index(t_700, t_850, dp_850)
    assert calculated == c_haines


@pytest.mark.parametrize(
    "c_haines_data, expected_mask_data, expected_severity_data",
    [
        ([[0, 1, 2, 3.9]], [[0, 0, 0, 0]], [[0, 0, 0, 0]]),
        ([[4, 5, 6, 7.9]], [[1, 1, 1, 1]], [[1, 1, 1, 1]]),
        ([[8, 9, 10, 10.9]], [[1, 1, 1, 1]], [[2, 2, 2, 2]]),
        ([[11, 12]], [[1, 1]], [[3, 3]]),
    ],
)
def test_calculate_severity(c_haines_data, expected_mask_data, expected_severity_data):
    result = generate_severity_data(c_haines_data)
    assert np.array_equal(result[1], expected_mask_data)
    assert np.array_equal(result[0], expected_severity_data)


@pytest.mark.parametrize(
    "tmp_700, tmp_850, dew_850, c_haines_data",
    [
        (
            "CMC_hrdps_continental_TMP_ISBL_0700_ps2.5km_2021012618_P048-00.grib2",
            "CMC_hrdps_continental_TMP_ISBL_0850_ps2.5km_2021012618_P048-00.grib2",
            "CMC_hrdps_continental_DEPR_ISBL_0850_ps2.5km_2021012618_P048-00.grib2",
            "c_haines_data.json.gz",
        ),
    ],
)
def test_c_haines_generator(tmp_700, tmp_850, dew_850, c_haines_data):
    tmp_700_path = get_complete_filename(__file__, tmp_700)
    tmp_850_path = get_complete_filename(__file__, tmp_850)
    dew_850_path = get_complete_filename(__file__, dew_850)
    c_haines_path = get_complete_filename(__file__, c_haines_data)

    with open_gdal(tmp_700_path, tmp_850_path, dew_850_path) as input_data:
        generator = CHainesGenerator()

        generated_c_haines = generator.generate_c_haines(input_data)

    with gzip.open(c_haines_path, "rt") as c_haines_file:
        expected_c_haines = json.load(c_haines_file)

    assert np.array_equal(generated_c_haines, expected_c_haines)


@pytest.mark.parametrize(
    "model, model_run_start, forecast_hour, expected_result",
    [
        (
            "GDPS",
            "00",
            "120",
            "https://dd.weather.gc.ca/today/model_gem_global/15km/grib2/lat_lon/00/120/",
        ),
        (
            "RDPS",
            "12",
            "010",
            "https://dd.weather.gc.ca/today/model_gem_regional/10km/grib2/12/010/",
        ),
        (
            "HRDPS",
            "00",
            "001",
            "https://dd.weather.gc.ca/today/model_hrdps/continental/grib2/00/001/",
        ),
    ],
)
def test_generate_url(model, model_run_start, forecast_hour, expected_result):
    assert make_model_run_base_url(model, model_run_start, forecast_hour) == expected_result


@pytest.mark.parametrize(
    "model, level, date, model_run_start, forecast_hour, expected_result",
    [
        (
            "HRDPS",
            "DEPR_ISBL",
            "2021012618",
            "048",
            "00",
            "CMC_hrdps_continental_DEPR_ISBL_ps2.5km_2021012618048_P00-00.grib2",
        ),
        (
            "RDPS",
            "DEPR_ISBL",
            "2021012618",
            "0",
            "12",
            "CMC_reg_DEPR_ISBL_ps10km_20210126180_P12.grib2",
        ),
        (
            "GDPS",
            "DEPR_ISBL",
            "2021012618",
            "0",
            "13",
            "CMC_glb_DEPR_ISBL_latlon.15x.15_20210126180_P13.grib2",
        ),
    ],
)
def test_generate_file_name(model, level, date, model_run_start, forecast_hour, expected_result):
    assert (
        make_model_run_filename(model, level, date, model_run_start, forecast_hour)
        == expected_result
    )


@pytest.mark.parametrize(
    "model, now, model_run_hour, prediction_hour, expected_urls, expected_model_run_timestamp, expected_prediction_timestamp",
    [
        (
            "HRDPS",
            "2021-03-11T16:46:11.600781",
            12,
            240,
            {
                "TMP_ISBL_0700": "https://dd.weather.gc.ca/today/model_hrdps/continental/grib2/12/240/CMC_hrdps_continental_TMP_ISBL_0700_ps2.5km_2021031112_P240-00.grib2",
                "TMP_ISBL_0850": "https://dd.weather.gc.ca/today/model_hrdps/continental/grib2/12/240/CMC_hrdps_continental_TMP_ISBL_0850_ps2.5km_2021031112_P240-00.grib2",
                "DEPR_ISBL_0850": "https://dd.weather.gc.ca/today/model_hrdps/continental/grib2/12/240/CMC_hrdps_continental_DEPR_ISBL_0850_ps2.5km_2021031112_P240-00.grib2",
            },
            "2021-03-11 12:00:00+00:00",
            "2021-03-21 12:00:00+00:00",
        ),
        (
            "RDPS",
            "2021-04-11T16:46:11.600781",
            12,
            240,
            {
                "TMP_ISBL_700": "https://dd.weather.gc.ca/today/model_gem_regional/10km/grib2/12/240/CMC_reg_TMP_ISBL_700_ps10km_2021041112_P240.grib2",
                "TMP_ISBL_850": "https://dd.weather.gc.ca/today/model_gem_regional/10km/grib2/12/240/CMC_reg_TMP_ISBL_850_ps10km_2021041112_P240.grib2",
                "DEPR_ISBL_850": "https://dd.weather.gc.ca/today/model_gem_regional/10km/grib2/12/240/CMC_reg_DEPR_ISBL_850_ps10km_2021041112_P240.grib2",
            },
            "2021-04-11 12:00:00+00:00",
            "2021-04-21 12:00:00+00:00",
        ),
        (
            "GDPS",
            "2021-05-11T16:46:11.600781",
            00,
            6,
            {
                "TMP_ISBL_700": "https://dd.weather.gc.ca/today/model_gem_global/15km/grib2/lat_lon/00/006/CMC_glb_TMP_ISBL_700_latlon.15x.15_2021051100_P006.grib2",
                "TMP_ISBL_850": "https://dd.weather.gc.ca/today/model_gem_global/15km/grib2/lat_lon/00/006/CMC_glb_TMP_ISBL_850_latlon.15x.15_2021051100_P006.grib2",
                "DEPR_ISBL_850": "https://dd.weather.gc.ca/today/model_gem_global/15km/grib2/lat_lon/00/006/CMC_glb_DEPR_ISBL_850_latlon.15x.15_2021051100_P006.grib2",
            },
            "2021-05-11 00:00:00+00:00",
            "2021-05-11 06:00:00+00:00",
        ),
    ],
)
def test_generate_urls_and_timestamps(
    model,
    now,
    model_run_hour,
    prediction_hour,
    expected_urls,
    expected_model_run_timestamp,
    expected_prediction_timestamp,
):
    now = datetime.fromisoformat(now)
    urls, model_run_timestamp, prediction_timestamp = make_model_run_download_urls(
        model, now, model_run_hour, prediction_hour
    )

    assert urls == expected_urls
    assert model_run_timestamp == datetime.fromisoformat(expected_model_run_timestamp)
    assert prediction_timestamp == datetime.fromisoformat(expected_prediction_timestamp)


@pytest.mark.parametrize(
    "input_geojson, expected_output_geojson, source_projection",
    [
        (
            "test_re_project_gdps_input.json",
            "test_re_project_gdps_expected_output.json",
            'GEOGCS["Coordinate System imported from GRIB file",DATUM["unnamed",SPHEROID["Sphere",6371229,0]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AXIS["Latitude",NORTH],AXIS["Longitude",EAST]]',
        ),
        (
            "test_re_project_rdps_input.json",
            "test_re_project_rdps_expected_output.json",
            'PROJCS["unnamed",GEOGCS["Coordinate System imported from GRIB file",DATUM["unnamed",SPHEROID["Sphere",6371229,0]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],PROJECTION["Polar_Stereographic"],PARAMETER["latitude_of_origin",60],PARAMETER["central_meridian",249],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Metre",1],AXIS["Easting",SOUTH],AXIS["Northing",SOUTH]]',
        ),
    ],
)
def test_reproject_geojson(input_geojson, expected_output_geojson, source_projection):
    input_geojson = get_complete_filename(__file__, input_geojson)
    expected_output_geojson = get_complete_filename(__file__, expected_output_geojson)

    dict_out = re_project_and_classify_geojson(input_geojson, source_projection)

    with open(expected_output_geojson) as expected_output_file:
        expected_json = json.load(expected_output_file)

        assert json.loads(json.dumps(dict_out)) == expected_json
