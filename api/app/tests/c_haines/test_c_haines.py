""" Test c_haines code.
"""
import json
from typing import List
from pytest_bdd import scenario, given, when, then
import numpy
from app.c_haines.severity_index import generate_severity_data
from app.c_haines.c_haines_index import calculate_c_haines_index


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
