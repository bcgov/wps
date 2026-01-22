
from typing import Any

from wps_shared.db.models.smurfi import Spot, RequestTypeEnum


class SpotService:

    async def create_spot(self, data) -> Spot:
        from wps_shared.db.database import get_async_write_session_scope

        spot = Spot(
            fire_number=data['fire_number'],
            request_id=data['metadata']['submissionId'],
            request_time=data['forecast_start_date'],
            end_time=data['forecast_end_date'],
            additional_info=data.get('additional_info', None),
            requested_type=data['spot_forecast_type'],
            requested_by=data['email'],
            status=RequestTypeEnum.Requested,
            #geographic_area_name= get from fire API call
            #fire_centre= get from fire API call
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
        )

        async with get_async_write_session_scope() as session:
            session.add(spot)
            await session.flush()  # Ensures spot.id is populated
        return spot
