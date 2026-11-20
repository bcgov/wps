import { DateTime } from 'luxon'
import { describe, expect, it } from 'vitest'
import type { MoreCast2Row } from './interfaces'
import { adjustStationTemperatures } from './temperatureAdjustment'

const row = (stationCode = 1, temperature = 20): MoreCast2Row =>
  ({
    stationCode,
    forDate: DateTime.utc().plus({ days: 1 }),
    tempHRDPS: temperature,
    tempActual: NaN,
    rhActual: NaN,
    precipActual: NaN,
    windDirectionActual: NaN,
    windSpeedActual: NaN,
    grassCuringActual: NaN
  }) as MoreCast2Row
const elevations = { stationElevation: 1000, modelElevations: { HRDPS: 500 } }

describe('adjustStationTemperatures', () => {
  it.each([
    [9.8, 15.1],
    [-9.8, 24.9],
    [0, 20]
  ])('applies rate %s from the original model', (rate, expected) => {
    const first = adjustStationTemperatures([row()], 1, 'HRDPS', rate, elevations)
    expect(first.rows[0].tempForecast?.value).toBeCloseTo(expected)
    expect(first.rows[0].tempForecast?.choice).toBe('MANUAL')
    expect(adjustStationTemperatures(first.rows, 1, 'HRDPS', rate, elevations).rows).toEqual(first.rows)
  })
  it('warms downward and preserves zero temperatures', () => {
    const result = adjustStationTemperatures([row(1, 0)], 1, 'HRDPS', 9.8, { ...elevations, stationElevation: 0 })
    expect(result.rows[0].tempForecast?.value).toBeCloseTo(4.9)
  })
  it('skips other stations, missing values, observations and past days', () => {
    const rows = [
      row(2),
      row(1, NaN),
      { ...row(), tempActual: 12 },
      { ...row(), forDate: DateTime.utc().minus({ days: 2 }) }
    ]
    expect(adjustStationTemperatures(rows, 1, 'HRDPS', 9.8, elevations).rows).toEqual([])
  })
  it('rejects the entire batch when a result is invalid', () => {
    expect(adjustStationTemperatures([row(), row(1, -60)], 1, 'HRDPS', 9.8, elevations).rows).toEqual([])
    expect(adjustStationTemperatures([row()], 1, 'HRDPS', NaN, elevations).rows).toEqual([])
    expect(adjustStationTemperatures([row()], 1, 'HRDPS', 9.8, undefined).rows).toEqual([])
  })
})
