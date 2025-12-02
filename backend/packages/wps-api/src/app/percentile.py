""" This module contains logic to get pre-calculated 90th percentile.
"""

import os
import logging
from statistics import mean
from fastapi import HTTPException, status
import wps_shared.schemas.percentiles

logger = logging.getLogger(__name__)


def get_precalculated_percentiles(request: wps_shared.schemas.percentiles.PercentileRequest):
    """ Return the pre calculated percentile response
    """
    # NOTE: percentile is ignored, all responses overridden to match
    # pre-calculated values; 90th percentile
    year_range_start = request.year_range.start
    year_range_end = request.year_range.end

    if len(request.stations) == 0 or request.stations is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Weather station is not found.')

    foldername = os.path.join(
        os.path.dirname(__file__), f"data/{year_range_start}-{year_range_end}")
    logger.info(foldername)

    if not os.path.exists(foldername):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='The year range is not currently supported.')

    response = wps_shared.schemas.percentiles.CalculatedResponse(percentile=90, year_range=wps_shared.schemas.percentiles.YearRange(start=year_range_start, end=year_range_end))

    bui = []
    isi = []
    ffmc = []
    for code in request.stations:
        filename = os.path.join(foldername, f"{code}.json")
        summary = wps_shared.schemas.percentiles.StationSummary.parse_file(filename)

        if summary.bui and summary.isi and summary.ffmc:
            bui.append(summary.bui)
            isi.append(summary.isi)
            ffmc.append(summary.ffmc)

        response.stations[code] = summary

    response.mean_values = wps_shared.schemas.percentiles.MeanValues()
    response.mean_values.bui = mean(bui) if bui else None
    response.mean_values.isi = mean(isi) if isi else None
    response.mean_values.ffmc = mean(ffmc) if ffmc else None

    return response
