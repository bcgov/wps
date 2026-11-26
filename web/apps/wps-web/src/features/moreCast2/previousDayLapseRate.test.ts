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
    [1300, 9.8],
    [1500, -9.8],
    [1299, 9.8],
    [1501, -9.8],
    [0, 2.1]
  ])('calculates using station elevation %s', (elevation, rate) => {
    expect(estimatePreviousDayLapseRate(data, 1, elevation, 'HRDPS', date).rate).toBe(rate)
  })
  it.each([
    [6.5, 6.5],
    [-6.5, -6.5],
    [9.8, 9.8],
    [-9.8, -9.8],
    [20.1, 9.8],
    [-20.1, -9.8],
    [9.74, 9.7],
    [-9.74, -9.7]
  ])('caps and rounds the automatic rate %s', (rawRate, expected) => {
    const sample = { ...data, actuals: [{ ...data.actuals[0], temperature: prediction.temperature! + rawRate * 0.5 }] }
    expect(estimatePreviousDayLapseRate(sample, 1, 900, 'HRDPS', date).rate).toBe(expected)
  })
  it.each([1340, 1460, 1300.01, 1499.99])('does not prefill below 100 m at elevation %s', elevation => {
    expect(estimatePreviousDayLapseRate(data, 1, elevation, 'HRDPS', date).rate).toBeNull()
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
