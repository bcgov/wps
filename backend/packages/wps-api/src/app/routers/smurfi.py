import logging

from fastapi import APIRouter


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/smurfi",
)


@router.post("/forecast")
async def create_smurfi_forecast(data: dict):
    logger.info("Received SMURFI forecast data")
    # Process the data as needed
    return {"status": "success", "data_received": data}
