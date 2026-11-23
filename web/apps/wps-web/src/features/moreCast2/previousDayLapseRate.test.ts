import type { WeatherIndeterminate, WeatherIndeterminatePayload } from '@wps/api/moreCast2API'
import { DateTime } from 'luxon'
import { estimatePreviousDayLapseRate } from './previousDayLapseRate'

const date = DateTime.fromISO('2026-11-22')
const prediction = {
  station_code: 1,
  determinate: 'HRDPS',
  utc_timestamp: '2026-11-22T20:00:00Z',
  temperature: 7,
  model_elevation: 1400
} as WeatherIndeterminate
const data: WeatherIndeterminatePayload = {
  predictions: [prediction],
  forecasts: [],
  grassCuring: [],
  actuals: [{ ...prediction, determinate: 'Actual', temperature: 10 }]
}

describe('previous day lapse rate', () => {
  it.each([
    [900, 6],
    [1900, -6],
    [1399, 3000],
    [0, 2.1]
  ])('calculates using station elevation %s', (elevation, rate) => {
    expect(estimatePreviousDayLapseRate(data, 1, elevation, 'HRDPS', date).rate).toBe(rate)
  })
  it('preserves zero temperatures and zero rates', () => {
    const zeros = {
      ...data,
      predictions: [{ ...prediction, temperature: 0 }],
      actuals: [{ ...data.actuals[0], temperature: 0 }]
    }
    expect(estimatePreviousDayLapseRate(zeros, 1, 900, 'HRDPS', date).rate).toBe(0)
  })
  it.each([null, Number.NaN, Number.POSITIVE_INFINITY, 1400])('rejects missing or equal elevations %s', elevation => {
    expect(estimatePreviousDayLapseRate(data, 1, elevation, 'HRDPS', date).rate).toBeNull()
  })
  it('requires matching station, raw model, and time', () => {
    expect(estimatePreviousDayLapseRate(data, 2, 900, 'HRDPS', date).rate).toBeNull()
    expect(estimatePreviousDayLapseRate(data, 1, 900, 'HRDPS_BIAS', date).rate).toBeNull()
    expect(estimatePreviousDayLapseRate(data, 1, 900, 'HRDPS', date.plus({ days: 1 })).rate).toBeNull()
  })
})
