import { ForecastsResponse } from 'api/forecastAPI'
import { RecursivePartial } from 'types/utilTypes'

export const mockStations = [
  { code: 1, name: 'Station 1', lat: '1', long: '1' },
  { code: 2, name: 'Station 2', lat: '2', long: '2' }
]

export const mockForecastsResponse: RecursivePartial<ForecastsResponse> = {
  forecasts: [
    {
      station: mockStations[0],
      values: [
        {
          datetime: '2020-04-30T12:00:00',
          temperature: 7.4,
          relative_humidity: 69,
          wind_direction: 230,
          wind_speed: 5,
          total_precipitation: 0
        }
      ]
    }
  ]
}
