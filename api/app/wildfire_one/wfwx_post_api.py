"""This module contains methods for submitting information to the WFWX Fireweather API."""

import logging
from typing import List
from aiohttp import ClientSession
from fastapi import status, HTTPException
from app import config
from app.schemas.morecast_v2 import WF1PostForecast
from app.wildfire_one.wfwx_api import get_auth_header

logger = logging.getLogger(__name__)

WF1_FORECAST_POST_URL = f"{config.get('WFWX_BASE_URL')}/v1/dailies/daily-bulk"
WF1_HTTP_ERROR = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="""
        Error submitting forecasts to WF1, please retry.
        All your forecast inputs have been saved as a draft on your browser and can be submitted at a later time.
        If the problem persists, use the following link to verify the status of the WF1 service: https://wfapps.nrs.gov.bc.ca/pub/wfwx-fireweather-web/stations
    """,
)


async def post_forecasts(session: ClientSession, forecasts: List[WF1PostForecast]):
    logger.info("Using WFWX to post/put forecasts")
    headers = await get_auth_header(session)

    forecasts_json = [forecast.model_dump() for forecast in forecasts]

    async with session.post(WF1_FORECAST_POST_URL, json=forecasts_json, headers=headers) as response:
        response_json = await response.json()
        if response.status == status.HTTP_201_CREATED or response.status == status.HTTP_200_OK:
            logger.info("submitted forecasts to wf1 %s.", response_json)
        else:
            logger.error(f"error submitting forecasts to wf1 {response_json}")
            raise WF1_HTTP_ERROR
