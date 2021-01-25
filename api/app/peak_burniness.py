""" This module contains logic to get pre-calculated 90th percentile.
"""

import os
import logging
from fastapi import HTTPException, status
import app.schemas.peak_burniness

logger = logging.getLogger(__name__)


def get_precalculated_peak_values(request: app.schemas.peak_burniness.PeakValuesRequest):
    """ Return the pre calculated peak values response
    """
    if len(request.stations) == 0 or request.stations is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Weather station is not found.')

    foldername = os.path.join(
        os.path.dirname(__file__), 'data/{}'.format(request.stations))
    logger.info(foldername)

    if not os.path.exists(foldername):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Request failed.')

    response = app.schemas.peak_burniness.CalculatedResponse()

    for code in request.stations:
        filename = os.path.join(foldername, '{}.json'.format(code))
        summary = app.schemas.peak_burniness.StationSummary.parse_file(filename)

        response.stations[code] = summary

    return response
