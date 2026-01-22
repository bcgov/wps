import logging

from fastapi import APIRouter
from wps_shared.schemas.smurfi import PullFromChefsResponse

from app.smurfi.download_chefs_data import get_chefs_submissions_json
from app.smurfi.spot import SpotService

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/smurfi",
)


@router.get("/pull_from_chefs", response_model=PullFromChefsResponse)
async def pull_from_chefs():
    processed_requests = get_chefs_submissions_json()
    spot_service = SpotService()

    created_spots = []
    for request_data in processed_requests:
        spot = await spot_service.create_spot(request_data)
        created_spots.append(spot)

    logger.info(f"Created {len(created_spots)} spots from CHEFS data")
    return PullFromChefsResponse(success=True)
