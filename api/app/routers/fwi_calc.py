""" Routers for FWI calculations.
"""
import logging
from fastapi import APIRouter, Depends
from app.auth import authentication_required
from app.schemas.fwi_calc import FWIOutputResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fwi-calc",
    dependencies=[Depends(authentication_required)],
)


@router.post('/', response_model=FWIOutputResponse)
async def get_fwi_calc_outputs(_=Depends(authentication_required)):
    """ Returns FWI calculations for all inputs """
    try:
        logger.info('/fwi_calc/')
        return FWIOutputResponse(fwi_outputs=[])
    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise
