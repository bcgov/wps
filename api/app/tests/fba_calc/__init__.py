""" Code common to fba tests
"""
from typing import Final
from decimal import Decimal
import logging


logger = logging.getLogger(__name__)

acceptable_margin_of_error: Final = 0.01
fire_size_acceptable_margin_of_error: Final = 0.02  # close, but using slightly different approach to RedAPP.


def relative_error(actual: float, expected: float, precision: int = 2):
    """ Calculate the relative error between two values - default to precision of 2."""
    actual = round(actual, precision)
    expected = round(expected, precision)
    if actual == expected:
        return 0
    if expected == 0:
        # Can't divide by 0! Taking this as a 100% difference
        return 1
    error = Decimal(abs((actual - expected) / expected))
    # we only care up to 2 decimal places at most.
    return float(round(error, precision))


def calculate_error(fuel_type, metric, metric_error_margin, python_value, comparison_value, note):
    """ Perform various calculations and checking of error between python_value
    and comparison_value. """
    margin_of_error = metric_error_margin
    if python_value < 2 and comparison_value < 2:
        logger.debug('when dealing with small numbers like %s and %s, we increase the margin of error',
                     python_value, comparison_value)
        margin_of_error = metric_error_margin * 4
    error = relative_error(python_value, comparison_value)
    if error > margin_of_error:
        logger.error('%s %s relative error %s > %s! (actual: %s, expected: %s)',
                     fuel_type, metric, error, margin_of_error, python_value, comparison_value)
    if metric_error_margin > margin_of_error:
        logger.warning('%s: The acceptable margin of error (%s) for %s is set too high',
                       fuel_type, metric_error_margin, metric)
    if error > metric_error_margin:
        absolute_error = abs(python_value - comparison_value)
        if absolute_error < margin_of_error:
            logger.info('no big deal, the absolute difference (%s) is tiny!', absolute_error)
        else:
            assert_message = (f"""{fuel_type}:{metric} {error} > {metric_error_margin} """
                              f"""(absolute error: {absolute_error}) ; actual: {python_value} """
                              f"""expected: {comparison_value}""")
            if note:
                assert_message += f' {note}'
            assert error < metric_error_margin, assert_message
    return error


def check_metric(metric: str,
                 fuel_type: str,
                 python_value: float,
                 comparison_value: float,
                 metric_error_margin: float,
                 note: str = None) -> float:
    """ Check relative error of a metric """
    # logging with %s became unreadable:
    if comparison_value is None:
        logger.warning('Skipping %s! (%s) - note: %s', metric, comparison_value, note)
    elif comparison_value < 0:
        logger.warning('Skipping %s! (%s) - note: %s', metric, comparison_value, note)
    else:
        assert python_value >= 0
        return calculate_error(fuel_type, metric, metric_error_margin, python_value, comparison_value, note)
