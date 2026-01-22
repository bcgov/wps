import logging

from fastapi import APIRouter
from wps_shared.db.models.smurfi import SpotRequestStatusEnum
from wps_shared.schemas.smurfi import PullFromChefsResponse

from app.smurfi.download_chefs_data import get_chefs_submissions_json
from app.smurfi.spot import SpotService
from wps_shared.schemas.smurfi import SmurfiSpotVersionData

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


@router.get("/smurfi_forecast/{spot_id}", response_model=SmurfiSpotVersionData)
async def smurfi_forecast(spot_id: int):
    spot_service = SpotService()
    forecast_data = await spot_service.get_forecast_data(spot_id)
    return forecast_data


@router.post("/create_spot_version/{spot_id}", response_model=int)
async def create_spot_version(spot_id: int, data: SmurfiSpotVersionData):
    spot_service = SpotService()
    spot_version_id = await spot_service.create_spot_version(spot_id, data)
    return spot_version_id


@router.post("/change_spot_status/{spot_id}/{new_status}", response_model=None)
async def change_spot_status(spot_id: int, new_status: SpotRequestStatusEnum):
    spot_service = SpotService()
    await spot_service.change_spot_status(spot_id, new_status)
