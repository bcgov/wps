import { DateTime } from 'luxon'
import { createEmptyMoreCast2Row } from 'features/moreCast2/slices/dataSlice'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { filterRowsForSimulationFromEdited, filterAllVisibleRowsForSimulation } from 'features/moreCast2/rowFilters'
import { ModelType } from 'api/moreCast2API'
import { rowIDHasher } from 'features/moreCast2/util'

const TEST_DATE = DateTime.fromISO('2023-02-16T20:00:00+00:00')

export const buildValidForecastRow = (
  stationCode: number,
  forDate: DateTime,
  choice: ModelType = 'FORECAST'
): MoreCast2Row => {
  const id = rowIDHasher(stationCode, forDate)
  const forecastRow = createEmptyMoreCast2Row(id, stationCode, 'stationName', forDate, 1, 2)
  forecastRow.precipForecast = { choice: choice, value: 2 }
  forecastRow.tempForecast = { choice: choice, value: 2 }
  forecastRow.rhForecast = { choice: choice, value: 2 }
  forecastRow.windSpeedForecast = { choice: choice, value: 2 }
  forecastRow.id = id

  return forecastRow
}

const buildValidActualRow = (stationCode: number, forDate: DateTime): MoreCast2Row => {
  const actualRow = createEmptyMoreCast2Row('id', stationCode, 'stationName', forDate, 1, 2)
  actualRow.precipActual = 1
  actualRow.tempActual = 1
  actualRow.rhActual = 1
  actualRow.windSpeedActual = 1

  return actualRow
}

const buildInvalidForecastRow = (stationCode: number, forDate: DateTime): MoreCast2Row => {
  const forecastRow = createEmptyMoreCast2Row('id', stationCode, 'stationName', forDate, 1, 2)

  return forecastRow
}

const actual1B = buildValidActualRow(1, TEST_DATE.minus({ days: 1 })) // exclude
const actual1A = buildValidActualRow(1, TEST_DATE) // include
const forecast1A = buildValidForecastRow(1, TEST_DATE.plus({ days: 1 })) // edited row
const forecast1B = buildValidForecastRow(1, TEST_DATE.plus({ days: 2 })) // include
const forecast1C = buildInvalidForecastRow(1, TEST_DATE.plus({ days: 3 })) // exclude

const actual2B = buildValidActualRow(2, TEST_DATE.minus({ days: 1 })) // exclude
const actual2A = buildValidActualRow(2, TEST_DATE) // include
const forecast2A = buildValidForecastRow(2, TEST_DATE.plus({ days: 1 })) // include
const forecast2B = buildValidForecastRow(2, TEST_DATE.plus({ days: 2 })) // include
const forecast2C = buildInvalidForecastRow(2, TEST_DATE.plus({ days: 3 })) // exclude
const forecast2D = buildInvalidForecastRow(2, TEST_DATE.plus({ days: 4 })) // exclude

const rows = [
  actual1A,
  actual1B,
  forecast1A,
  forecast1B,
  forecast1C,
  actual2A,
  forecast2A,
  actual2B,
  forecast2B,
  forecast2C,
  forecast2D
]

describe('filterRowsForSimulationFromEdited', () => {
  const filteredRows = filterRowsForSimulationFromEdited(forecast1A, rows)
  it('should filter for valid rows before and after the edited row ', () => {
    expect(filteredRows).toEqual(expect.arrayContaining([actual1A, forecast1A, forecast1B]))
  })
  it('should not contain invalid forecasts', () => {
    expect(filteredRows).not.toContain(forecast1C)
  })
  it('should not contain unnecessary actuals', () => {
    expect(filteredRows).not.toContain(actual1B)
  })
  it('should not contain rows from other stations', () => {
    expect(filteredRows).not.toContain(forecast2A)
    expect(filteredRows).not.toContain(forecast2B)
    expect(filteredRows).not.toContain(actual2A)
  })
  it('should return undefined if yesterday does not contain a valid row', () => {
    actual1A.precipActual = NaN
    const filteredRows = filterRowsForSimulationFromEdited(forecast1A, rows)
    expect(filteredRows).toBe(undefined)
  })
})
describe('filterAllVisibleRowsForSimulation', () => {
  const filteredRows = filterAllVisibleRowsForSimulation(rows)
  it('should only include valid forecasts and most recent actuals for each station', () => {
    expect(filteredRows).toEqual(
      expect.arrayContaining([actual1A, forecast1A, forecast1B, actual2A, forecast2A, forecast2B])
    )
  })
  it('should not contain invalid forecasts', () => {
    expect(filteredRows).not.toContain(forecast1C)
    expect(filteredRows).not.toContain(forecast2C)
    expect(filteredRows).not.toContain(forecast2D)
  })
  it('should not contain unnecessary actuals', () => {
    expect(filteredRows).not.toContain(actual2B)
    expect(filteredRows).not.toContain(actual1B)
  })
  it('should return undefined if there are no valid forecasts', () => {
    const rows = [actual1A, forecast1C, forecast2C, forecast2D]
    const filteredRows = filterAllVisibleRowsForSimulation(rows)
    expect(filteredRows).toBe(undefined)
  })
})
