"""Routers for SFMS Next Generation data."""

from fastapi import APIRouter, Depends
from wps_shared.auth import audit, authentication_required
from wps_shared.db.crud.sfms_run import get_sfms_insights_bounds
from wps_shared.db.database import get_async_read_session_scope
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
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
    for year, run_type, min_date, max_date in results:
        run_type_key = run_type.value if isinstance(run_type, RunTypeEnum) else run_type
        year_bounds = sfms_bounds.setdefault(year, {})
        year_bounds[run_type_key] = SFMSBoundsDateRange(minimum=min_date, maximum=max_date)

    return SFMSBoundsResponse(sfms_bounds=sfms_bounds)
