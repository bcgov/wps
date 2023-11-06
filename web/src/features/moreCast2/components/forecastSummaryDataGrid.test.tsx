import { filterRowsForSimulationFromEdited } from 'features/moreCast2/components/ForecastSummaryDataGrid'
import { DateTime } from 'luxon'
import { createEmptyMoreCast2Row } from 'features/moreCast2/slices/dataSlice'
import { MoreCast2Row } from 'features/moreCast2/interfaces'

const TEST_DATE = DateTime.fromISO('2023-02-16T20:00:00+00:00')

const buildValidForecastRow = (stationCode: number, forDate: DateTime): MoreCast2Row => {
  const forecastRow = createEmptyMoreCast2Row('id', stationCode, 'stationName', forDate, 1, 2)
  forecastRow.precipForecast = { choice: 'FORECAST', value: 2 }
  forecastRow.tempForecast = { choice: 'FORECAST', value: 2 }
  forecastRow.rhForecast = { choice: 'FORECAST', value: 2 }
  forecastRow.windSpeedForecast = { choice: 'FORECAST', value: 2 }

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

// rows to filter in
const actual1A = buildValidActualRow(1, TEST_DATE)
const forecast1A = buildValidForecastRow(1, TEST_DATE.plus({ days: 1 })) // edited row
const forecast1B = buildValidForecastRow(1, TEST_DATE.plus({ days: 2 }))

// rows to filter out
const actual1B = buildValidActualRow(1, TEST_DATE.minus({ days: 1 }))
const forecast1C = buildInvalidForecastRow(1, TEST_DATE.plus({ days: 3 }))
const actual2A = buildValidActualRow(2, TEST_DATE.minus({ days: 1 }))
const forecast2A = buildValidForecastRow(2, TEST_DATE.plus({ days: 1 }))

const rows = [actual1A, actual1B, forecast1A, forecast1B, forecast1C, actual2A, forecast2A]

describe('filterRowsForSimulationFromEdited', () => {
  it('should filter for valid rows before and after the edited row', () => {
    const filteredRows = filterRowsForSimulationFromEdited(forecast1A, rows)
    expect(filteredRows).toEqual(expect.arrayContaining([actual1A, forecast1A, forecast1B]))
    expect(filteredRows).not.toEqual(expect.arrayContaining([actual1B, forecast1C, actual2A, forecast2A]))
  })
})
