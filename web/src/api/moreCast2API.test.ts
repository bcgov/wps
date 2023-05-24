import {
  marshalMoreCast2ForecastRecords,
  submitMoreCastForecastRecords,
  fetchWeatherIndeterminates,
  WeatherDeterminate
} from 'api/moreCast2API'
import axios from 'api/axios'
import { DateTime } from 'luxon'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'

describe('moreCast2API', () => {
  const buildMorecast2Forecast = (
    id: string,
    stationCode: number,
    stationName: string,
    forDate: DateTime
  ): MoreCast2ForecastRow => ({
    id,
    stationCode,
    stationName,
    forDate,
    precip: { choice: 'FORECAST', value: 0 },
    rh: { choice: 'FORECAST', value: 0 },
    temp: { choice: 'FORECAST', value: 0 },
    windDirection: { choice: 'FORECAST', value: 0 },
    windSpeed: { choice: 'FORECAST', value: 0 }
  })
  it('should marshall forecast records correctly', async () => {
    const res = marshalMoreCast2ForecastRecords([
      buildMorecast2Forecast('1', 1, 'one', DateTime.fromObject({ year: 2021, month: 1, day: 1 })),
      buildMorecast2Forecast('2', 2, 'two', DateTime.fromObject({ year: 2021, month: 1, day: 1 }))
    ])
    expect(res).toHaveLength(2)
    expect(res[0].station_code).toBe(1)
    expect(res[0].for_date).toEqual(DateTime.fromObject({ year: 2021, month: 1, day: 1 }).toMillis())
    expect(res[0].precip).toEqual(0)
    expect(res[0].temp).toEqual(0)
    expect(res[0].rh).toEqual(0)
    expect(res[0].wind_speed).toEqual(0)
    expect(res[0].wind_direction).toEqual(0)

    expect(res[1].station_code).toBe(2)
    expect(res[1].for_date).toEqual(DateTime.fromObject({ year: 2021, month: 1, day: 1 }).toMillis())
    expect(res[1].precip).toEqual(0)
    expect(res[1].temp).toEqual(0)
    expect(res[1].rh).toEqual(0)
    expect(res[1].wind_speed).toEqual(0)
    expect(res[1].wind_direction).toEqual(0)
  })
  it('should call submit endpoint for forecast submission', async () => {
    axios.post = jest.fn().mockResolvedValue({ status: 201 })
    const res = await submitMoreCastForecastRecords('testToken', [
      buildMorecast2Forecast('1', 1, 'one', DateTime.fromObject({ year: 2021, month: 1, day: 1 })),
      buildMorecast2Forecast('2', 2, 'two', DateTime.fromObject({ year: 2021, month: 1, day: 1 }))
    ])
    expect(res).toBe(true)
  })
  it('should fetch weather indeterminates with no stations requested', async () => {
    const res = await fetchWeatherIndeterminates(
      [],
      DateTime.fromObject({ year: 2021, month: 1, day: 1 }),
      DateTime.fromObject({ year: 2021, month: 1, day: 2 })
    )
    expect(JSON.stringify(res)).toBe(JSON.stringify({ actuals: [], forecasts: [], predictions: [] }))
  })

  it('should fetch weather indeterminates with stations requested', async () => {
    const response = {
      data: {
        actuals: [
          {
            id: '1',
            station_code: 1,
            station_name: 'one',
            determinate: WeatherDeterminate.ACTUAL,
            utc_timestamp: DateTime.fromObject({ year: 1970, month: 1, day: 1 }).toMillis(),
            precipitation: 1,
            relative_humidity: 1,
            temperature: 1,
            wind_direction: 1,
            wind_speed: 1
          }
        ],
        forecasts: [
          {
            id: '2',
            station_code: 2,
            station_name: 'two',
            determinate: WeatherDeterminate.FORECAST,
            for_date: DateTime.fromObject({ year: 1970, month: 1, day: 1 }).toMillis(),
            temp: 2,
            rh: 2,
            precip: 2,
            wind_direction: 2,
            wind_speed: 2
          }
        ],
        predictions: [
          {
            id: '3',
            station_code: 3,
            station_name: 'three',
            determinate: WeatherDeterminate.GDPS,
            utc_timestamp: DateTime.fromObject({ year: 1970, month: 1, day: 1 }).toMillis(),
            precipitation: 3,
            relative_humidity: 3,
            temperature: 3,
            wind_direction: 3,
            wind_speed: 3
          }
        ]
      }
    }
    axios.post = jest.fn().mockResolvedValue(response)
    const res = await fetchWeatherIndeterminates(
      [1, 2, 3],
      DateTime.fromObject({ year: 1970, month: 1, day: 1 }),
      DateTime.fromObject({ year: 1970, month: 1, day: 2 })
    )

    const expected = {
      actuals: response.data.actuals,
      forecasts: [
        {
          id: '',
          station_code: 2,
          station_name: 'two',
          determinate: WeatherDeterminate.FORECAST,
          utc_timestamp: '1970-01-01T20:00:00+00:00',
          precipitation: 2,
          relative_humidity: 2,
          temperature: 2,
          wind_direction: 2,
          wind_speed: 2
        }
      ],
      predictions: response.data.predictions
    }
    expect(JSON.stringify(res)).toBe(JSON.stringify(expected))
  })
})
