""" Routers for new/formal/non-tinker fba.
"""
import logging
from fastapi import APIRouter, Response, Depends
from app.auth import authentication_required, audit
from app.schemas.fba import FireCenterListResponse
from app.wildfire_one.wfwx_api import (get_fire_centers)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fba",
    dependencies=[Depends(authentication_required), Depends(audit)],
)


@router.get('/fire-centers', response_model=FireCenterListResponse)
async def get_daily_view(response: Response,
                         _=Depends(authentication_required)):
    """ Returns daily metrics for each station code. """
    try:
        logger.info('/fba/fire-centers')
        response.headers["Cache-Control"] = "max-age=0"  # don't let the browser cache this
        fire_centers = await get_fire_centers()
        return FireCenterListResponse(fire_centers=fire_centers)
    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise
