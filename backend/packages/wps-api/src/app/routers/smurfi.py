


import logging

from fastapi import APIRouter

from app.smurfi.download_chefs_data import get_chefs_submissions_json
from wps_shared.schemas.smurfi import PullFromChefsResponse


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/smurfi",
)

@router.get("/pull_from_chefs", response_model=PullFromChefsResponse)
async def pull_from_chefs():
    get_chefs_submissions_json()
    return PullFromChefsResponse(success=True)
    