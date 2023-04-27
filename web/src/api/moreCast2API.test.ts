import { marshalMoreCast2ForecastRecords, submitMoreCastForecastRecords } from 'api/moreCast2API'
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
    const res = await submitMoreCastForecastRecords([
      buildMorecast2Forecast('1', 1, 'one', DateTime.fromObject({ year: 2021, month: 1, day: 1 })),
      buildMorecast2Forecast('2', 2, 'two', DateTime.fromObject({ year: 2021, month: 1, day: 1 }))
    ])
    expect(res).toBe(true)
  })
})
