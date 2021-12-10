""" Routers for new/formal/non-tinker fba.
"""
import logging
from fastapi import APIRouter, Depends
from aiohttp.client import ClientSession
from app.auth import authentication_required, audit
from app.routers.fba_calc import get_stations_data
from app.schemas.fba import FireCenterListResponse
from app.wildfire_one.wfwx_api import (get_auth_header, get_fire_centers)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fba",
    dependencies=[Depends(authentication_required), Depends(audit)],
)


@router.get('/fire-centers/', response_model=FireCenterListResponse)
async def get_all_fire_centers(_=Depends(authentication_required)):
    """ Returns fire centers for all active stations. """
    try:
        logger.info('/fba/fire-centers/')
        async with ClientSession() as session:
            header = await get_auth_header(session)
            fire_centers = await get_fire_centers(session, header)
        return FireCenterListResponse(fire_centers=fire_centers)
    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise
