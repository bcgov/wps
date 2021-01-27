""" This module contains logic to get pre-calculated 90th percentile.
"""

import os
import json
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

    response = app.schemas.peak_burniness.CalculatedResponse()

    for code in request.stations:
        foldername = os.path.join(os.path.dirname(__file__), 'data/peakValues/')
        filename = os.path.join(foldername, '{}.json'.format(code))
        logger.info(filename)

        if not os.path.exists(filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Request failed.')

        summary = parse_json_file(filename)

        response.stations[code] = summary

    return response


def parse_json_file(filename: str):
    """ Parse the station's JSON file into StationSummary object
    """
    with open(filename) as results_file:
        data = json.load(results_file)

    months = {
        '04': 'April ',
        '5': 'May ',
        '6': 'June ',
        '7': 'July ',
        '8': 'August ',
        '9': 'September '
    }

    station_summaries = list()

    for index in range(30):
        station_summary = app.schemas.peak_burniness.StationSummary()
        station_summary.max_temp = data['median_max_temp'][str(index)]
        station_summary.min_rh = data['median_min_rh'][str(index)]
        station_summary.max_wind_speed = data['median_max_wind_speed'][str(index)]
        station_summary.max_ffmc = data['median_max_ffmc'][str(index)]
        station_summary.max_fwi = data['median_max_fwi'][str(index)]
        station_summary.hour_max_temp = data['median_max_temp_hour'][str(index)]
        station_summary.hour_min_rh = data['median_min_rh_hour'][str(index)]
        station_summary.hour_max_wind_speed = data['median_max_wspeed_hour'][str(index)]
        station_summary.hour_max_ffmc = data['median_max_ffmc_hour'][str(index)]
        station_summary.hour_max_fwi = data['median_max_fwi_hour'][str(index)]
        start_day = data['start_day'][str(index)]
        if int(start_day) == 0:
            start_day = '01'
        end_day = data['end_day'][str(index)]
        if int(end_day) > 31:
            end_day = '31'
        station_summary.week = months[data['month'][str(
            index)]] + start_day + '-' + end_day
        station_summaries.append(station_summary)

    return station_summaries
