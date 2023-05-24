""" This module contains methods for submitting information to the WFWX Fireweather API.
"""
import logging
from typing import List
from aiohttp import ClientSession
from app import config
from app.schemas.morecast_v2 import WF1PostForecast

logger = logging.getLogger(__name__)

WF1_FORECAST_POST_URL = f"{config.get('WFWX_BASE_URL')}/v1/dailies/daily-bulk"


async def post_forecasts(session: ClientSession,
                         wf1Token: str,
                         forecasts: List[WF1PostForecast]):

    logger.info('Using WFWX to post/put forecasts')
    headers = {'Authorization': f"Bearer {wf1Token}"}

    async with session.post(WF1_FORECAST_POST_URL, data={forecasts}, headers=headers) as response:
        response_json = await response.json()
        logger.info('submitted forecasts to wf1 %s.', response_json)
