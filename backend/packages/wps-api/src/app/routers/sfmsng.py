"""Routers for SFMS Next Generation data."""

from fastapi import APIRouter, Depends
from wps_shared.auth import audit, authentication_required
from wps_shared.db.crud.sfms_run import get_sfms_insights_bounds
from wps_shared.db.database import get_async_read_session_scope
from wps_shared.schemas.fba import SFMSBoundsByYear, SFMSBoundsDateRange, SFMSBoundsResponse

router = APIRouter(
    prefix="/sfmsng",
    dependencies=[Depends(authentication_required), Depends(audit)],
)


@router.get("/run-bounds", response_model=SFMSBoundsResponse)
async def get_sfmsng_run_bounds():
    async with get_async_read_session_scope() as session:
        results = await get_sfms_insights_bounds(session)

    sfms_bounds: SFMSBoundsByYear = {}
    for bounds in results:
        year_bounds = sfms_bounds.setdefault(bounds.year, {})
        year_bounds[bounds.run_type.value] = SFMSBoundsDateRange(
            minimum=bounds.minimum, maximum=bounds.maximum
        )

    return SFMSBoundsResponse(sfms_bounds=sfms_bounds)
