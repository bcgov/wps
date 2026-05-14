import logging

from fastapi import APIRouter, Depends
from wps_shared.auth import asa_authentication_required, audit_asa
from wps_shared.schemas.psu import FireCentresResponse

from app.psu.fire_centres import build_psu_fire_centres_response, fetch_fire_centres

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/psu",
    dependencies=[Depends(asa_authentication_required), Depends(audit_asa)],
)


@router.get("/fire-centres", response_model=FireCentresResponse)
async def get_all_fire_centres():
    logger.info("/psu/fire-centres")
    fire_centres = await fetch_fire_centres()
    return build_psu_fire_centres_response(fire_centres)
