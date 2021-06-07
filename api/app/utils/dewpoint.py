""" This module contains functions related to dewpoint.
"""

import math
import logging

logger = logging.getLogger(__name__)


def compute_dewpoint(temp, relative_humidity):
    """ Computes dewpoint based on code from the legacy system.
        See: https://chat.developer.gov.bc.ca/channel/wildfire-wfwx?msg=vzjt28hWCP9J5pZtK
    """
    logger.debug("Computing dewpoint for temp: %s and rh: %s", temp, relative_humidity)
    return (temp - (14.55 + 0.114 * temp) *
            (1 - (0.01 * relative_humidity)) -
            math.pow(((2.5 + 0.007 * temp) *
                      (1 - (0.01 * relative_humidity))), 3) - (15.9 + 0.117 * temp) *
            math.pow((1 - (0.01 * relative_humidity)), 14))
