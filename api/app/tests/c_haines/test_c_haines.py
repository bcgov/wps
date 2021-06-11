""" Test c_haines code.
"""
import json
import gzip
import os
from datetime import datetime
from typing import List
import tempfile
from pytest_bdd import scenario, given, when, then
import numpy
from app.c_haines.severity_index import (
    generate_severity_data, open_gdal, make_model_run_base_url, make_model_run_filename,
    make_model_run_download_urls, re_project_and_classify_geojson)
from app.weather_models import ModelEnum
from app.c_haines.c_haines_index import calculate_c_haines_index, CHainesGenerator
from app.tests import get_complete_filename


@scenario(
    'test_c_haines.feature',
    'Calculate c-haines',
    example_converters=dict(t_850=float, t_700=float, dp_850=float, c_haines=float))
def test_extract_origin_and_pixel_information():
    """ BDD Scenario. """


@then('With <t_850> <t_700> and <dp_850>, I expect <c_haines>')
def with_temperature_and_dewpoint_values(t_850, t_700, dp_850, c_haines):
    """ Open the dataset. """
    calculated = calculate_c_haines_index(t_700, t_850, dp_850)
    assert calculated == c_haines


@scenario(
    'test_c_haines.feature',
    'Calculate severity',
    example_converters=dict(
        c_haines_data=json.loads,
        mask_data=json.loads,
        severity_data=json.loads))
def test_calculate_mask_and_severity():
    """ BDD Scenario. """


@given('<c_haines_data>', target_fixture='collector')
def given_data(c_haines_data):
    """ Given data in some scenario, create a collector. """
    return {'c_haines_data': c_haines_data}


@when('generating severity')
def generate_data(collector: dict):
    """ Generate a result, and stick it in the collector. """
    result = generate_severity_data(collector['c_haines_data'])
    collector['severity_data'] = result[0]
    collector['mask_data'] = result[1]


@then('We expect <mask_data>')
def then_expect_mask_data(mask_data: List, collector: dict):
    """ Assert that mask is as expected """
    assert (numpy.array(collector['mask_data']) == numpy.array(mask_data)).all()


@then('We expect <severity_data>')
def then_expect_severity_data(severity_data: List, collector: dict):
    """ Assert that severity is as expected """
    assert (numpy.array(collector['severity_data']) == numpy.array(severity_data)).all()


@scenario(
    'test_c_haines.feature',
    'Generate c-haines data',
    example_converters=dict(
        tmp_700=str,
        tmp_850=str,
        dew_850=str,
        c_haines_data=str))
def test_generate_c_haines():
    """ BDD Scenario. """


@given("<tmp_700>, <tmp_850> and <dew_850>", target_fixture='collector')
def given_grib_files(tmp_700, tmp_850, dew_850):
    """ Given grib files for calculating c-haines. """
    return {
        'tmp_700': get_complete_filename(__file__, tmp_700),
        'tmp_850': get_complete_filename(__file__, tmp_850),
        'dew_850': get_complete_filename(__file__, dew_850)}


@when("We generate c-haines")
def generate_c_haines(collector):
    """ Generate c-haines data using grib files. """
    with open_gdal(collector['tmp_700'], collector['tmp_850'], collector['dew_850']) as gdal_data:
        generator = CHainesGenerator()
        # Generate c-haines data. It's pretty slow.
        collector['data'] = generator.generate_c_haines(gdal_data)


@then("We expect <c_haines_data>")
def check_c_haines(collector, c_haines_data):
    """ Compare the c-haines data against expected data.

    This data generated with this code:

    import json
    import gzip
    from app.c_haines.severity_index import open_gdal
    from app.c_haines.c_haines_index import CHainesGenerator

    with open_gdal(tmp_700, tmp_850, dew_850) as gdal_data:
        generator = CHainesGenerator()
        data = generator.generate_c_haines(gdal_data)
        with gzip.open('data.json.gz', 'wt') as f:
            json.dump(data, f)
    """
    filename = get_complete_filename(__file__, c_haines_data)
    with gzip.open(filename, 'rt') as c_haines_data_file:
        data = json.load(c_haines_data_file)
    assert (numpy.array(collector['data']) == numpy.array(data)).all()


@scenario(
    'test_c_haines.feature',
    'Make model run base url',
    example_converters=dict(
        model=str,
        model_run_start=str,
        forecast_hour=str))
def test_make_model_run_base_url():
    """ BDD Scenario. """


@then("make_model_run_base_url(<model>, <model_run_start>, <forecast_hour>) == <result>")
def make_model_run_base_url_expect_result(model, model_run_start, forecast_hour, result):
    """ Check base url """
    assert make_model_run_base_url(model, model_run_start, forecast_hour) == result


@scenario(
    'test_c_haines.feature',
    'Make model run filename',
    example_converters=dict(
        model=str,
        level=str,
        date=str,
        model_run_start=str,
        forecast_hour=str,
        result=str))
def test_make_model_run_filename():
    """ BDD Scenario. """


@then("make_model_run_filename(<model>, <level>, <date>, <model_run_start>, <forecast_hour>) == <result>")
def make_model_run_filename_expect_result(model, level, date, model_run_start, forecast_hour, result):
    """ Check base url """
    assert make_model_run_filename(model, level, date, model_run_start, forecast_hour) == result


@scenario(
    'test_c_haines.feature',
    'Make model run download urls',
    example_converters=dict(
        model=str,
        now=datetime.fromisoformat,
        model_run_hour=int,
        prediction_hour=int,
        urls=json.loads,
        model_run_timestamp=datetime.fromisoformat,
        prediction_timestamp=datetime.fromisoformat))
def test_make_model_download_urls():
    """ BDD Scenario. """


@given("We run make_model_run_download_urls(<model>, <now>, <model_run_hour>, <prediction_hour>)",
       target_fixture='collector')
def run_make_model_run_download_urls(
        model: ModelEnum, now: datetime, model_run_hour: int, prediction_hour: int):
    """ Collect url's """
    urls, model_run_timestamp, prediction_timestamp = make_model_run_download_urls(
        model, now, model_run_hour, prediction_hour)
    return {
        'urls': urls,
        'model_run_timestamp': model_run_timestamp,
        'prediction_timestamp': prediction_timestamp
    }


@then("<urls> are as expected")
def make_model_run_download_urls_expect_result(
        collector: dict, urls: dict):
    """ Assert that result matches expected result """
    assert urls == collector['urls']


@then("<model_run_timestamp> is as expected")
def make_model_run_download_model_run_timestamp_expect_result(collector: dict,
                                                              model_run_timestamp: datetime):
    """ Assert that result matches expected result """
    assert model_run_timestamp == collector['model_run_timestamp']


@then("<prediction_timestamp> is as expected")
def make_model_run_download_prediction_timestamp_expect_result(collector: dict,
                                                               prediction_timestamp: datetime):
    """ Assert that result matches expected result """
    assert prediction_timestamp == collector['prediction_timestamp']


@scenario(
    'test_c_haines.feature',
    'Re-project',
    example_converters=dict(
        input_geojson=str,
        expected_output_geojson=str))
def test_re_project():
    """ BDD Scenario. """


@given("<input_geojson> with <source_projection> and <expected_output_geojson>", target_fixture='collector')
def prepare_input(input_geojson: str, source_projection: str, expected_output_geojson: str):
    """ Collect url's """
    return {
        'input_geojson': input_geojson,
        'source_projection': source_projection,
        'expected_output_geojson': expected_output_geojson
    }


@then("Compare expected geojson with actual")
def compare_expected_output(collector: dict):
    """ Assert that result matches expected result """

    input_geojson = get_complete_filename(__file__, collector['input_geojson'])
    source_projection = collector['source_projection']

    dict_out = re_project_and_classify_geojson(input_geojson, source_projection)

    expected_output_geojson = get_complete_filename(__file__, collector['expected_output_geojson'])

    with open(expected_output_geojson) as expected_output_file:
        expected_json = json.load(expected_output_file)
        # silly chain for comparison:  not a json dict-> json string -> json dict
        assert json.loads(json.dumps(dict_out)) == expected_json
