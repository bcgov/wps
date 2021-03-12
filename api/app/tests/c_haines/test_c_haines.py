""" Test c_haines code.
"""
import json
import gzip
from typing import List
from pytest_bdd import scenario, given, when, then
import numpy
from app.c_haines.severity_index import (
    generate_severity_data, open_gdal, make_model_run_base_url, make_model_run_filename)
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
