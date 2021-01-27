""" Test c_haines code.
"""
from pytest_bdd import scenario, then
from app.c_haines.c_haines_index import calculate_c_haines_index


@scenario(
    'test_c_haines.feature',
    'Calculate c-haines',
    example_converters=dict(t_850=float, t_700=float, dp_850=float, c_haines=float))
def test_extract_origin_and_pixel_information():
    """ BDD Scenario. """


@then('With <t_850> <t_700> and <dp_850>, I expect <c_haines>')
def given_grib_file(t_850, t_700, dp_850, c_haines):
    """ Open the dataset. """
    calculated = calculate_c_haines_index(t_700, t_850, dp_850)
    assert calculated == c_haines
