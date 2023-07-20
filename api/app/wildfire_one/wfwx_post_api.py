""" This module contains methods for submitting information to the WFWX Fireweather API.
"""
import logging
from typing import List
from aiohttp import ClientSession, ClientConnectionError
from app import config
from app.schemas.morecast_v2 import WF1PostForecast

logger = logging.getLogger(__name__)

WF1_FORECAST_POST_URL = f"{config.get('WFWX_BASE_URL')}/v1/dailies/daily-bulk"


async def post_forecasts(session: ClientSession,
                         token: str,
                         forecasts: List[WF1PostForecast]):

    logger.info('Using WFWX to post/put forecasts')
    headers = {'Authorization': f"Bearer {token}"}

    forecasts_json = [forecast.dict() for forecast in forecasts]

    async with session.post(WF1_FORECAST_POST_URL, json=forecasts_json, headers=headers) as response:
        response_json = await response.json()
        if response.status >= 400:
            logger.error(f'error submitting forecasts to wf1 {response_json}')
            raise ClientConnectionError
        logger.info('submitted forecasts to wf1 %s.', response_json)
