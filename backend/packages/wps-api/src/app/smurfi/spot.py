
from typing import Any
import sqlalchemy as sa
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.smurfi import Spot, SpotRequestStatusEnum, SpotVersion
from wps_shared.schemas.smurfi import SmurfiForecastData, SmurfiGeneralForecastData, SmurfiSpotVersionData


class SpotService:

    async def create_spot(self, data) -> Spot:

        spot = Spot(
            fire_number=data['fire_number'],
            request_id=data['metadata']['submissionId'],
            request_time=data['forecast_start_date'],
            end_time=data['forecast_end_date'],
            additional_info=data.get('additional_info', None),
            requested_type=data['spot_forecast_type'],
            requested_by=data['email'],
            status=SpotRequestStatusEnum.Requested,
            #geographic_area_name= get from fire API call
            #fire_centre= get from fire API call
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
        )

        async with get_async_write_session_scope() as session:
            session.add(spot)
            await session.flush()  # Ensures spot.id is populated
        return spot
    
    async def change_spot_status(self, spot_id: int, new_status: SpotRequestStatusEnum) -> None:
        async with get_async_write_session_scope() as session:
            await session.execute(
                sa.update(Spot)
                .where(Spot.id == spot_id)
                .values(status=new_status)
            )
        return
    
    async def create_spot_version(self, spot_id: int, data: SmurfiSpotVersionData) -> int:
        async with get_async_write_session_scope() as session:
            # Set is_latest=False for any existing SpotVersion with this spot_id
            await session.execute(
                sa.update(SpotVersion)
                .where(SpotVersion.spot_id == spot_id, SpotVersion.is_latest == True)
                .values(is_latest=False)
            )

            spot_version = SpotVersion(
                spot_id=spot_id,
                forecaster=data.forecaster,
                forecaster_email=data.forecaster_email,
                forecaster_phone=data.forecaster_phone,
                representative_weather_stations=data.representative_weather_stations,
                latitude=data.latitude,
                longitude=data.longitude,
                elevation=data.elevation,
                fire_size=data.fire_size,
                slope=data.slope,
                aspect=data.aspect,
                valley=data.valley,
                synopsis=data.synopsis,
                inversion_and_venting=data.inversion_and_venting,
                outlook=data.outlook,
                confidence=data.confidence,
                additional_fire_numbers=data.additional_fire_numbers,
                is_latest=True,
            )
            session.add(spot_version)
            await session.flush()
        return spot_version.id
    
    async def get_forecast_data(self, spot_id: int) -> SmurfiSpotVersionData:
        async with get_async_write_session_scope() as session:
            spot_result = await session.execute(
                sa.select(Spot).where(Spot.id == spot_id)
            )
            spot = spot_result.scalars().first()
            result = SmurfiSpotVersionData(
                spot_id=spot.id,
                fire_number=spot.fire_number,
                requested_by=spot.requested_by,
                geographic_area_name=spot.geographic_area_name,
                fire_centre=spot.fire_centre,
                latitude=spot.latitude,
                longitude=spot.longitude,
                fire_size=spot.fire_size,
            )

            spot_version_result = await session.execute(
                sa.select(SpotVersion).where(SpotVersion.spot_id == spot_id and SpotVersion.is_latest == True)
            )
            spot_version = spot_version_result.scalars().first()
            if spot_version:
                result.forecaster = spot_version.forecaster
                result.elevation = spot_version.elevation
                result.representative_weather_stations = spot_version.representative_weather_stations
                result.forecaster_email = spot_version.forecaster_email
                result.forecaster_phone = spot_version.forecaster_phone
                result.additional_fire_numbers = spot_version.additional_fire_numbers
                result.valley = spot_version.valley
                result.synopsis = spot_version.synopsis
                result.inversion_and_venting = spot_version.inversion_and_venting
                result.outlook = spot_version.outlook
                result.confidence = spot_version.confidence

                result.forecasts = [
                    SmurfiForecastData(
                        forecast_time=forecast.forecast_time,
                        temperature=forecast.temperature,
                        relative_humidity=forecast.relative_humidity,
                        wind=forecast.wind,
                        probability_of_precipitation=forecast.probability_of_precipitation,
                        precipitation_amount=forecast.precipitation_amount,
                    )
                    for forecast in spot_version.forecasts
                ]
                result.general_forecasts = [
                    SmurfiGeneralForecastData(
                        period=general_forecast.period,
                        temperature=general_forecast.temperature,
                        relative_humidity=general_forecast.relative_humidity,
                        conditions=general_forecast.conditions,
                    )
                    for general_forecast in spot_version.general_forecasts
                ]
                if spot_version.latitude:
                    result.latitude = spot_version.latitude
                if spot_version.longitude:
                    result.longitude = spot_version.longitude
                if spot_version.fire_size:
                    result.fire_size = spot_version.fire_size

        return result
