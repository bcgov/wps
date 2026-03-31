from typing import Sequence

from wps_shared.db.crud.psu import get_fire_centres as get_db_fire_centres
from wps_shared.db.database import get_async_read_session_scope
from wps_shared.db.models.psu import FireCentre as DBFireCentre
from wps_shared.schemas.fba import (
    FireCenterListResponse,
)
from wps_shared.schemas.psu import FireCentre, FireCentresResponse


async def fetch_fire_centres() -> list[DBFireCentre]:
    async with get_async_read_session_scope() as session:
        result = await get_db_fire_centres(session)
        return list(result)


def build_fire_centre_items(fire_centres: Sequence[DBFireCentre]) -> list[FireCentre]:
    return [FireCentre(id=item.id, name=item.name) for item in fire_centres]


def build_psu_fire_centres_response(
    fire_centres: Sequence[DBFireCentre],
) -> FireCentresResponse:
    return FireCentresResponse(fire_centres=build_fire_centre_items(fire_centres))


def build_fba_fire_centers_response(
    fire_centres: Sequence[DBFireCentre],
) -> FireCenterListResponse:
    """
    Included for now because ASA Go expects the spelling in the response to be "fire_centers" instead of "fire_centres".
    This can be removed once ASA Go is updated to use the same spelling as the rest of the codebase.
    ASA Go is currently released as version 1.0.2 on ios and version 1.0 on android
    """
    return FireCenterListResponse(fire_centers=build_fire_centre_items(fire_centres))
