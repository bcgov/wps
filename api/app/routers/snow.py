""" Routers for Snow related data
"""

import logging
from datetime import date, datetime
from fastapi import APIRouter, Depends
from wps_shared.auth import authentication_required, audit
from wps_shared.db.crud.snow import get_most_recent_processed_snow_by_date
from wps_shared.db.database import get_async_read_session_scope
from wps_shared.schemas.snow import ProcessedSnowModel, ProcessedSnowResponse
from wps_shared.utils.time import vancouver_tz

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/snow",
    dependencies=[Depends(authentication_required), Depends(audit)],
)


@router.get('/most-recent-by-date/{for_date}', response_model=ProcessedSnowResponse | None)
async def get_most_recent_by_date(for_date: date, _=Depends(authentication_required)):
    """ Returns the most recent processed snow record before or equal to the provided date. """
    logger.info('/snow/most-recent-by-date/')
    tz_aware_datetime = vancouver_tz.localize(datetime.combine(for_date, datetime.min.time()))
    async with get_async_read_session_scope() as session:
        result = await get_most_recent_processed_snow_by_date(session, tz_aware_datetime)
        if result is not None:
            processed_snow = result[0]
            return ProcessedSnowResponse(processed_snow=ProcessedSnowModel(for_date=processed_snow.for_date, processed_date=processed_snow.processed_date, snow_source=processed_snow.snow_source))