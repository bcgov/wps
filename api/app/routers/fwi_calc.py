""" Routers for FWI calculations.
"""
import logging
import random
from fastapi import APIRouter, Depends
from app.auth import authentication_required
from app.utils.time import get_hour_20_from_date
from app.schemas.fwi_calc import FWIRequest, FWIOutput, FWIOutputResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fwi-calc",
    dependencies=[Depends(authentication_required)],
)


@router.post('/', response_model=FWIOutputResponse)
async def get_fwi_calc_outputs(request: FWIRequest, _=Depends(authentication_required)):
    """ Returns FWI calculations for all inputs """
    try:
        logger.info('/fwi_calc/')
        test = get_hour_20_from_date(request.date)
        output = FWIOutput(
            datetime=get_hour_20_from_date(request.date),
            ffmc=random.randint(0, 100),
            dmc=random.randint(0, 100),
            dc=random.randint(0, 100),
            isi=random.randint(0, 100),
            bui=random.randint(0, 100),
            fwi=random.randint(0, 100))
        return FWIOutputResponse(fwi_outputs=[output])
    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise
