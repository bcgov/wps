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

describe('adjustStationTemperatures', () => {
  it('combines models and preserves existing zero forecasts', () => {
    const rows = [row(), { ...row(1, NaN), tempECMWF: 15 }]
    const first = adjustStationTemperatures(rows, 1, 'HRDPS', -1)
    expect(first.rows).toHaveLength(1)
    const second = adjustStationTemperatures([first.rows[0], rows[1]], 1, 'ECMWF', 2)
    expect(second.rows).toHaveLength(1)
    expect(second.rows[0].tempForecast?.value).toBe(17)
    expect(second.message).toContain('Skipped 1 days with existing forecasts.')
    const occupied = { ...row(1, -60), tempForecast: { choice: 'MANUAL' as const, value: 0 } }
    expect(adjustStationTemperatures([occupied], 1, 'HRDPS', -1).rows).toEqual([])
    expect(adjustStationTemperatures([occupied], 1, 'HRDPS', 1, true).rows[0].tempForecast?.value).toBe(-59)
    const empty = { ...occupied, tempForecast: { ...occupied.tempForecast, value: NaN } }
    expect(adjustStationTemperatures([empty], 1, 'HRDPS', 1).rows).toHaveLength(1)
  })

  it.each([
    [-4.9, 15.1],
    [4.9, 24.9],
    [0, 20]
  ])('applies adjustment %s from the original model', (adjustment, expected) => {
    const first = adjustStationTemperatures([row()], 1, 'HRDPS', adjustment)
    expect(first.rows[0].tempForecast?.value).toBeCloseTo(expected)
    expect(first.rows[0].tempForecast?.choice).toBe('MANUAL')
    expect(adjustStationTemperatures(first.rows, 1, 'HRDPS', adjustment).rows).toEqual([])
    expect(adjustStationTemperatures(first.rows, 1, 'HRDPS', adjustment, true).rows).toEqual(first.rows)
  })
  it('warms downward and preserves zero temperatures', () => {
    const result = adjustStationTemperatures([row(1, 0)], 1, 'HRDPS', 4.9)
    expect(result.rows[0].tempForecast?.value).toBeCloseTo(4.9)
  })
  it('skips other stations, missing values, observations and past days', () => {
    const rows = [
      row(2),
      row(1, NaN),
      { ...row(), tempActual: 12 },
      { ...row(), forDate: DateTime.utc().minus({ days: 2 }) }
    ]
    expect(adjustStationTemperatures(rows, 1, 'HRDPS', 4.9).rows).toEqual([])
  })
  it('rejects the entire batch when a result is invalid', () => {
    expect(adjustStationTemperatures([row(), row(1, -60)], 1, 'HRDPS', -4.9).rows).toEqual([])
    expect(adjustStationTemperatures([row()], 1, 'HRDPS', NaN).rows).toEqual([])
  })
})
