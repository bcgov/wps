from app.schemas.morecast_v2 import YesterdayDaily


async def yesterday_observation_list_mapper(raw_dailies):
    """ Maps raw stations to WeatherStation list"""
    dailies = []
    async for raw_daily in raw_dailies:
        dailies.append(
            YesterdayDaily(
                temperature=raw_daily.get('temperature', None),
                status=raw_daily.get('recordType', '').get('id', None),
                relative_humidity=raw_daily.get('relativeHumidity', None),
                precipitation=raw_daily.get('precipitation', None),
                wind_direction=raw_daily.get('windDirection', None),
                wind_speed=raw_daily.get('windSpeed', None)
            )
        )
    return dailies
